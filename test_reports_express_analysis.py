import random
import pytest
import time
from flaky import flaky
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from API_Tests.BasicMetod.BasicMetod import get_id
from API_Tests.BasicMetod.authorization import globalauth
from Locators.basic_locators import *
from API_Tests.BasicMetod.model import delete_model, delete_client
from API_Tests.BasicMetod.version import waiting_service_results, delete_version_model
from UI_Tests.ReportsTests.ReportsHelpers.Express_analys_page import change_titles, check_axis, move_to_options, \
    not_active_checkbox, moving_slider, diff_cashflows, check_graph_options
from UI_Tests.ReportsTests.ReportsHelpers.Reports_page import select_model_and_vm_in_report, click_button_in_left_menu
from Test_Data.UI_variables_data import check_graph_titles, T_60, option_list
from API_Tests.Generator.create_model import create_model_with_certain_values
from API_Tests.Generator.create_version import upload_version_to_certain_model
from UI_Tests.UI_base import check_file_in_downloads, delete_file_in_downloads, step_authorization
import allure


@pytest.fixture(scope='module', autouse=True)
def setup_module(auth):
    with allure.step("Создание карточки модели"):
        global NEW_MODEL
        global MODEL_NAME
        global VM_ID
        global CLIENT_ID
        NEW_MODEL, MODEL_NAME, resp, model_obj = create_model_with_certain_values(
            auth, clientsegment='CIB', dealtype="Прочие сделки", structurers=[
                'analytic_login', 'underwriter_login', 'auditor_login', 'business_admin_login',
                'ar_quality_control_user_login',
                'credit_manager_login', 'portfolio_emloyee_login', 'monitoring_user_login'])
        CLIENT_ID = get_id(auth['cms'],
                           query=f"select R_CLIENTS_ID from L_MODELCLIENTS_CLIENTS where MODELS_ID={NEW_MODEL}")
        with allure.step(f"Загрузка ВМ в созданную модель {NEW_MODEL}"):
            VM_ID = upload_version_to_certain_model(auth, resp, NEW_MODEL, 'Group_reports_block.xlsx',
                                                    disabledvalidation=True)
    with allure.step(f"Проверка прохождения анализа зависимостей для {MODEL_NAME}"):
        state_id = waiting_service_results(auth, corr_id=VM_ID, upload_time=auth['upload_time'], service_type=7)
        assert state_id == 4, 'Анализ зависимостей не прошел'
    yield
    with allure.step('Удаление Модели, Клиента и ВМ'):
        resp = globalauth(auth, login=auth[f'system_login'], password=auth[f'system_pass'])
        del_mv = delete_version_model(auth, VM_ID, resp)
        assert del_mv.status_code == 200
        assert del_mv.json()['Status'] == 0, 'Версия модели не удалилась'
        del_model = delete_model(auth, NEW_MODEL, resp)
        assert del_model.status_code == 200
        assert del_model.json()['Status'] == 0, 'Модель не удалилась'
        del_client = delete_client(auth, CLIENT_ID, resp)
        assert del_client.status_code == 200
        del_client_id = get_id(auth['cms'],
                               query=f"select ID from CLIENTS where ID={CLIENT_ID}")
        assert del_client_id is None, 'Клиент не был удален из базы'


@pytest.mark.smoke_ui_test
@pytest.mark.ui_test
@pytest.mark.parametrize("role", ['business_admin',
                                  'credit_manager',
                                  pytest.param('auditor',
                                               marks=pytest.mark.xfail(reason="Внести учетную запись FinAuditor")),
                                  'portfolio_emloyee',
                                  'monitoring_user',
                                  'underwriter',
                                  'analytic',
                                  'ar_quality_control_user'])
@flaky(max_runs=3)
@allure.testcase(url='http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/21027',
                 name='Отчеты.Экспресс-анализ')
def test_express_anlys(auth, role, initial_driver):
    """Отчеты.Экспресс-анализ
           Author: Макаренков Александр Валерьевич"""
    with allure.step('Открыть форму Отчеты'):
        driver = initial_driver
        step_authorization(auth, driver, login=role + '_login', passw=role + '_pass', url_locator=url_reports[0],
                           title='Отчеты')
    with allure.step('Открыть форму экспресс-анализа'):
        WebDriverWait(driver, T_60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_express_analysis_dropdown)))
        select_model_and_vm_in_report(driver, MODEL_NAME)
        click_button_in_left_menu(auth, driver, role, button_name='Экспресс-анализ модели')
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_button_export)))
        ppt_button = driver.find_element_by_css_selector(css_button_export)
        assert ppt_button is not None, "Кнопка выгрузки ppt отсутствует"
        graph_titles = driver.find_elements_by_css_selector(css_graph_titles)
        graph_titles = [i.text for i in graph_titles]
        assert graph_titles.sort() == check_graph_titles.sort(), "Наименования графиков отличаются от ожидаемых"
        graph_options = [driver.find_element_by_id(id_check_options.format(i)) for i in range(3, 11)]
        assert len(graph_options) == 8, "У графиков отсутствуют необходимые опции"
    with allure.step('Открыть настройки графиков Рентабельность ebitda, рентабельность чистой прибыли'):
        move_to_options(driver=driver)
        change_titles(driver=driver,
                      dropdown_options=css_common_options.format("Рентабельность EBITDA и чистой прибыли"),
                      assert_statement='Рентабельность EBITDA и чистой прибыли')
        check_axis(driver=driver, locator_axis=css_axis, axis_left_options='Выберите параметр',
                   axis_right_options='EBITDA margin, Рентабельность чистой прибыли')
        checkboxes_show_values = driver.find_elements_by_css_selector(css_checkbox_active)
        assert len(
            checkboxes_show_values) == 4, ' На странице отсутствует необходимое количество чек-боксов Показать значение'
    with allure.step('Открыть настройки графиков Денежные потоки'):
        change_titles(driver=driver, dropdown_options=css_common_options.format("Денежные потоки"),
                      assert_statement='Денежные потоки')
        check_axis(driver=driver, locator_axis=css_axis, axis_left_options='NCF',
                   axis_right_options='Операционный CF, Инвестиционный CF, Финансовый CF')
        checkboxes_show_values = driver.find_elements_by_css_selector(css_checkbox_active)
        assert len(
            checkboxes_show_values) == 4, ' На странице отсутствует необходимое количество чек-боксов Показать значение'
        checkboxes_CAGR = driver.find_elements_by_css_selector(css_checkbox_cagr)
        assert len(checkboxes_CAGR) == 4, 'На странице отсутствует необходимое количество чек-боксов CAGR'
    with allure.step('Снять выделение с чекбокса Показать значение'):
        rand_index1, rand_index2 = random.sample({7, 9, 11, 13}, 2)
        collect_not_active_checkboxes = []
        first_not_active = not_active_checkbox(driver, rand_index1)
        second_not_active = not_active_checkbox(driver, rand_index2)
        collect_not_active_checkboxes.extend([first_not_active, second_not_active])
        assert len(collect_not_active_checkboxes) == 2
    with allure.step('Выбрать чек-бокс CAGR'):
        for i in range(0, 4):
            checkboxes_CAGR[i].click()
        cagr_options = driver.find_elements_by_css_selector(css_cagr_options)
        years = {}
        for i in range(1, 5):
            cagr_options[i - 1].click()
            WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, diff_cashflows[i])))
            option_cagr = driver.find_element_by_css_selector(diff_cashflows[i])
            ac = ActionChains(driver)
            ac.move_to_element(option_cagr.wrapped_element).click().perform()
            WebDriverWait(driver, T_60).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, css_cagr_dropdown)))
        for j in [7, 9, 11, 13]:
            moving_slider(driver, css_slider.format(j, 3), css_slider.format(j, 2))
            year_right = driver.find_element_by_css_selector(css_slider_year_right.format(j)).text
            year_left = driver.find_element_by_css_selector(css_slider_year_left.format(j)).text
            years[i] = [year_left, year_right]
            graphs = driver.find_elements_by_css_selector(css_cagr_graphs)
        for i in range(0, 4):
            graphs[i].click()
        for i in [6, 8, 10, 12]:
            cagr_ellipse = WebDriverWait(driver, T_60).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, css_cagr_ellipse.format(i))))
            assert cagr_ellipse is not None, ' CAGR отсутствует на графике'
            cagr_left = driver.find_element_by_css_selector(css_left_right_line.format(i, 2)).get_attribute('x1')
            circle_left = driver.find_element_by_css_selector(css_left_circle.format(i, 4)).get_attribute('cx')
            cagr_right = driver.find_element_by_css_selector(css_left_right_line.format(i, 3)).get_attribute('x1')
            circle_right = driver.find_element_by_css_selector(css_left_circle.format(i, 10)).get_attribute('cx')
            assert cagr_left == circle_left, "Диапазон CAGR не соответствует фильтрам"
            assert cagr_right == circle_right, "Диапазон CAGR не соответствует фильтрам"
            check_graph_options(driver, ind_option=i, option_list=option_list, locator=css_cagr_option_gragh)
    with allure.step('Нажимаем выгрузить в PowerPoint'):
        ppt_button.click()
        time.sleep(10)
    with allure.step('Проверка файлов в папке downloads'):
        check_file_in_downloads(startswith_file=f"Exported charts", extension_file=".pptx")
    with allure.step('Удаление файлов в папке downloads'):
        delete_file_in_downloads(startswith_file=f"Exported charts", extension_file=".pptx")
