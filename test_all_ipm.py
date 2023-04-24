import pytest
import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from API_Tests.BasicMetod.DB_queries import get_id_by_title
from API_Tests.BasicMetod.authorization import globalauth
from API_Tests.BasicMetod.basic_method import get_request
from API_Tests.BasicMetod.scenario import create_calc_request
from API_Tests.BasicMetod.BasicMetod import get_id
from API_Tests.BasicMetod.version import unblock_mv
from Test_Data.UI_variables_data import T_60, BUTTON_IN_LEFT_MENU, IPM_CREATE_ROLES, IPM_SEND_APPROVE_ROLES, \
    IPM_APPROVE_ROLES, IPM_ALL_TESTS, IPM_ACTUALITY_DEAL_ROLE
from UI_Tests.ReportsTests.ReportsHelpers.Reports_page import click_button_in_left_menu, select_model_and_vm_in_report, \
    check_ipm_state, ipm_rollback
from UI_Tests.UI_authorization import UIAuth
from UI_Tests.UI_base import step_authorization
from Locators.basic_locators import *
from Test_Data.API_variables_data import BASE_IPM, IPM_YEAR
import flaky


@pytest.fixture(scope='module', autouse=True)
def setup_module(auth):
    global TEST_PASSED, VM_ID, NEW_MODEL
    TEST_PASSED = {role: None for role in IPM_ALL_TESTS}
    VM_ID = get_id_by_title(auth, BASE_IPM['model_version'], 'MODEL_VERSIONS')
    NEW_MODEL = get_id_by_title(auth, BASE_IPM['model_name'], 'MODELS')
    resp = globalauth(auth, login=auth[f'business_admin_login'], password=auth[f'business_admin_pass'])
    unblock_mv(auth, VM_ID, resp)
    yield
    unblock = unblock_mv(auth, VM_ID, resp)
    assert unblock.status_code == 200, 'Разблокировка модели не произошла'


@pytest.mark.smoke_ui_test
@pytest.mark.ui_test
@flaky.flaky(max_runs=3)
@pytest.mark.parametrize("role", IPM_CREATE_ROLES)
@pytest.mark.dependency(name='ipm_creation')
@allure.testcase(url='http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/32416', name='ИПМ. Создание')
def test_ipm_create(auth, role, initial_driver):
    """В рамках теста используется глобальная переменная TEST_PASSED(dict) значениям которой присваивается 'IPM_CREATED'
    при прохождении теста под соответствующей ролью
    Author: Макаренков Александр Валерьевич"""
    with allure.step("Проверка предусловия"):
        resp = globalauth(auth, login=auth[f'business_admin_login'], password=auth[f'business_admin_pass'])
        check_ipm_state(auth, resp, BASE_IPM['model_version'])
        ipm_id = get_id(auth['cms'], query=f"SELECT ID FROM IPMS WHERE MODEL_VERSION_ID = '{VM_ID}'")
        get_request(auth, url_reports_delete_ipm.format(ipm_id), resp)
        unblock_mv(auth, VM_ID, resp)

    with allure.step(f"Заказ расчет для модели {BASE_IPM['model_name']}"):
        scenario_id = get_id(auth['cms'],
                             query="select ID from SCENARIOS where TYPE_ID = 1 and SCENARIO_SOURCE != 1 order by PUBLISH_DATE desc, ID desc offset 1 row fetch next 1 rows only")
        click_create_calc_request_button = create_calc_request(auth, scenario_id=scenario_id,
                                                               version_id=str(VM_ID),
                                                               response=resp)
        assert click_create_calc_request_button.status_code == 200, 'Расчет не был создан'
    with allure.step('Открыть форму Отчеты'):

        driver = initial_driver
        step_authorization(auth, driver, login=role + '_login', passw=role + '_pass')
    with allure.step('Открыть форму ИПМ'):
        driver.get(
            auth['protocol'] + auth['url'] + url_reports[0])
        WebDriverWait(driver, T_60).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, css_button_in_left_menu.format(BUTTON_IN_LEFT_MENU['ИПМ']))))
        click_button_in_left_menu(auth, driver, role, button_name='ИПМ')
        WebDriverWait(driver, T_60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_ipm_dropdown)))
        select_model_and_vm_in_report(driver, BASE_IPM['model_name'])
        driver.find_element_by_css_selector(css_select_vm).click()
        WebDriverWait(driver, T_60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_ipm_vm_dropdown[1])))
        vm_selector = driver.find_element_by_css_selector(css_ipm_vm_dropdown[1])
        vm_selector.send_keys(BASE_IPM['model_version'])
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_ipm_vm_dropdown[2])))
        driver.find_element_by_css_selector(css_ipm_vm_dropdown[2]).click()
        WebDriverWait(driver, T_60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_ipm_create))).click()
        WebDriverWait(driver, T_60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_ipm_table)))
        ipm_dropdowns = driver.find_elements_by_css_selector(css_ipm_table_dropdowns)
        assert len(ipm_dropdowns) == 4, 'Не вкладке отсутствуют необходимые дропдауны'
        ipm_intervals = driver.find_elements_by_css_selector(css_ipm_interval)
        assert len(ipm_intervals) == 3, 'Не вкладке отсутствуют кнопки выбора интервала'
    with allure.step('Нажать + Input / Нажать + Output'):
        for button in [1, 3]:
            driver.find_element_by_css_selector(css_ipm_add_input.format(button)).click()
            WebDriverWait(driver, T_60).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, css_ipm_add_row.format(button))))
            WebDriverWait(driver, T_60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_ipm_add_row.format(button))))
        ipm_first_column = [i.text for i in driver.find_elements_by_css_selector(css_ipm_first_column)]
        assert 'Input 2\n(Годовой)' in ipm_first_column, 'В таблицу IPM не был добавлен соответствующий input'
        assert 'Output 3' in ipm_first_column, 'В таблицу IPM не был добавлен соответствующий output'
    with allure.step('Выбрать параметры для строк'):
        indicators = driver.find_elements_by_css_selector(css_indicator_name)
        for i in (range(len(indicators))):
            indicators[i].click()
            WebDriverWait(driver, T_60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_indicator_input)))
            driver.find_elements_by_css_selector(css_indicator_dropdown[0])[0].click()
            WebDriverWait(driver, T_60).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, css_indicator_dropdown[1])))
            indicators = driver.find_elements_by_css_selector(css_indicator_name)
        indicators = [i.text for i in indicators]
        plus = driver.find_elements_by_css_selector(css_ipm_plus)
        for i in range(len(plus)):
            plus = driver.find_elements_by_css_selector(css_ipm_plus)
            plus[0].click()
            WebDriverWait(driver, T_60).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, css_indicator_dropdown[1])))
            driver.find_elements_by_css_selector(css_ipm_radiobuttons)[0].click()
        ipm_intervals_unsaved = driver.find_elements_by_css_selector(css_ipm_intervals)
        ipm_intervals_unsaved = [i.text for i in ipm_intervals_unsaved]
    with allure.step('Изменить дату окончания мониторинга'):
        periods = driver.find_elements_by_css_selector(css_ipm_periods)
        driver.find_element_by_css_selector(css_ipm_period_change[0]).click()
        WebDriverWait(driver, T_60).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_ipm_period_change[1])))
        periods_dropdown = Select(driver.find_element_by_css_selector(css_ipm_period_change[1]))
        periods_dropdown.select_by_visible_text(IPM_YEAR)
        driver.find_element_by_css_selector(css_ipm_december).click()
        periods_new = driver.find_elements_by_css_selector(css_ipm_periods)
        assert len(periods) - len(periods_new) == 16, 'Убранные периоды отображены в таблице'
        assert driver.find_element_by_css_selector(css_ipm_period_change[
                                                       2]).text == '12.{} - 12.{} Изменить'.format(
            str(int(IPM_YEAR) - 1), IPM_YEAR), 'Дата окончания мониторинга не изменилась'
    with allure.step('Указать дату начала эксплуатации'):
        driver.find_element_by_css_selector(css_date_of_use[0]).click()
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_date_of_use[3])))
        driver.find_element_by_css_selector(css_date_of_use[4]).click()
        driver.find_element_by_css_selector(css_date_of_use[5]).click()
        assert driver.find_element_by_css_selector(
            css_date_of_use[6]).text == '01.{} Изменить'.format(IPM_YEAR), 'Дата эксплуатации не выбрана'
    with allure.step('Нажать сохранить'):
        WebDriverWait(driver, T_60).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_ipm_save_button))).click()
        popup = WebDriverWait(driver, T_60).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_popup_ipm)))
        WebDriverWait(driver, T_60).until(EC.staleness_of(popup))
        assert driver.find_element_by_css_selector(css_ipm_statuses[
                                                       0]).text == 'Черновик', 'Статус не соответствует черновику'
        assert driver.find_element_by_css_selector(css_ipm_period_change[
                                                       2]).text == '12.{} - 12.{} Изменить'.format(
            str(int(IPM_YEAR) - 1), IPM_YEAR), 'Дата окончания мониторинга не изменилась после Сохранения'
        WebDriverWait(driver, T_60).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_ipm_statuses[1]))).click()
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_ipm_table_left)))
        indicators_saved = driver.find_elements_by_css_selector(css_choosen_indicators)
        indicators_saved = [i.text for i in indicators_saved]
        assert set(indicators).issubset(set(indicators_saved)), 'Отображаются не те показатели'
        ipm_intervals_saved = driver.find_elements_by_css_selector(css_ipm_intervals)
        ipm_intervals_saved = [i.text for i in ipm_intervals_saved]
        assert ipm_intervals_unsaved.sort() == ipm_intervals_saved.sort(), 'Отображаются не те интервалы'
        TEST_PASSED[role] = 'IPM_CREATED'


@pytest.mark.smoke_ui_test
@pytest.mark.ui_test
@flaky.flaky(max_runs=3)
@allure.testcase(url='http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/35358',
                 name='ИПМ. Отправка на согласование')
@pytest.mark.parametrize("role", IPM_SEND_APPROVE_ROLES)
def test_ipm_send_approve(auth, role, initial_driver):
    """В рамках теста используется глобальная переменная TEST_PASSED(dict) значениям которой присваивается 'SENT_TO_APPROVE'
    при прохождении теста под соответствующей ролью
    Author: Макаренков Александр Валерьевич"""
    if ([TEST_PASSED[i] for i in IPM_CREATE_ROLES].count('IPM_CREATED') != 4) and\
            (([TEST_PASSED[i] for i in IPM_CREATE_ROLES].count('IPM_CREATED') +
              [TEST_PASSED[i] for i in IPM_CREATE_ROLES].count('SENT_TO_APPROVE')) != 4):
        pytest.skip(f"Тест test_ipm_send_approve-ИПМ.отправка на согласование для роли {role} не пройден")
    ipm_id = get_id(auth['cms'], query=f"SELECT ID FROM IPMS WHERE MODEL_VERSION_ID = '{VM_ID}'")
    ipm_status = get_id(auth['cms'], query=f"SELECT  STATUS_ID FROM IPMS WHERE MODEL_VERSION_ID = '{VM_ID}'")
    if ipm_status != 1:
        ipm_rollback(auth, ipm_id, VM_ID, BASE_IPM['model_version'], 1)
    with allure.step('Блокирование ВМ'):
        driver = initial_driver
        step_authorization(auth, driver, login=role + '_login', passw=role + '_pass')
        driver.get(auth['protocol'] + auth['url'] + url_reports[5].format(NEW_MODEL, VM_ID))
        WebDriverWait(driver, T_60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_lock_vm))).click()
        block = WebDriverWait(driver, T_60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_block_vm)))
        assert ' '.join(driver.find_element_by_css_selector(
            css_lock_text).text.split()) in (
                   'Перед отправкой формы ИПМ на согласование убедитесь, что внесённые изменения сохранены.',
                   'Перед отправкой формы ИПМ на согласование убедитесь, что внесенные изменения сохранены и CF-модель '
                   'находится в статусе «Заблокирована»'), 'Нерпавильное сообщение при отправке на согласование'
        block.click()
        try:
            WebDriverWait(driver, T_60).until(EC.staleness_of(block))
        except TimeoutException:
            WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_block_vm))).click()
        WebDriverWait(driver, T_60).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, css_panda)))
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.XPATH, xpath_text.format(' На согласовании '))))
    with allure.step('Отправка на согласование'):
        assert driver.find_element_by_css_selector(
            css_ipm_statuses[0]).text == 'На согласовании', 'ВМ не перешла в статус На согласовании'
        driver.get(
            auth['protocol'] + auth['url'] + url_model_version.format(NEW_MODEL, VM_ID) + '&versionsPageIndex=2')
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_vm_status)))
        assert driver.find_element_by_css_selector(
            css_vm_status).text == 'Заблокирована', 'ВМ не перешла в статус Заблокирована'
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_ipm_form[0])))
        assert driver.find_element_by_css_selector(
            css_ipm_form[1]).text == 'На согласовании', 'ИПМ не перешел в статус На согласовании'
        with allure.step("Выход из АС CF"):
            UIAuth(driver=driver).logout(auth=auth, driver=driver)
        TEST_PASSED[role] = 'SENT_TO_APPROVE'
        if [TEST_PASSED[i] for i in IPM_SEND_APPROVE_ROLES].count('SENT_TO_APPROVE') < len(IPM_SEND_APPROVE_ROLES):
            ipm_id = get_id(auth['cms'], query=f"SELECT ID FROM IPMS WHERE MODEL_VERSION_ID = '{VM_ID}'")
            ipm_rollback(auth, ipm_id, VM_ID, BASE_IPM['model_version'], 1)
            resp = globalauth(auth, login=auth[f'business_admin_login'], password=auth[f'business_admin_pass'])
            unblock_mv(auth, VM_ID, resp)


@pytest.mark.smoke_ui_test
@pytest.mark.ui_test
@flaky.flaky(max_runs=3)
@allure.testcase(url='http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/33113', name='ИПМ.Согласование')
@pytest.mark.parametrize("role", IPM_APPROVE_ROLES)
def test_ipm_approve(auth, role, initial_driver):
    """В рамках теста используется глобальная переменная TEST_PASSED(dict) значениям которой присваивается 'IPM_APPROVED'
    при прохождении теста под соответствующей ролью
    Author: Макаренков Александр Валерьевич"""
    with allure.step('Открыть форму Модели под ролью Андеррайтера'):
        if [TEST_PASSED[i] for i in IPM_SEND_APPROVE_ROLES].count('SENT_TO_APPROVE') != 2:
            pytest.skip(f"Тест test_ipm_approve -ИПМ. Согласование для роли {role} не пройден")
        driver = initial_driver
        step_authorization(auth, driver, login=role + '_login', passw=role + '_pass')
        driver.get(auth['protocol'] + auth['url'] + url_model_version.format(NEW_MODEL, VM_ID) + '&versionsPageIndex=2')
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_ipm_form[0])))
        assert driver.find_element_by_css_selector(
            css_ipm_form[1]).text == 'На согласовании', 'Статус ИПМ на форме ВМ не соответствует ожидаемому'
    with allure.step('Нажать на кнопку Принять решение'):
        driver.find_element_by_id(id_make_decision).click()
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_confirm_window)))
    with allure.step('Нажать на кнопку Утвердить'):
        window = driver.find_element_by_css_selector(css_confirm_window)
        window.find_element_by_id(id_confirm).click()
        WebDriverWait(driver, T_60).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_approve_mv)))
        approve_mv = driver.find_element_by_css_selector(css_approve_mv)
        ActionChains(driver).move_to_element(approve_mv.wrapped_element).click().perform()
    with allure.step('Нажать на кнопку Отклонить'):
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_confirm_window)))
        window = driver.find_element_by_css_selector(css_confirm_window)
        window.find_element_by_css_selector(css_reject).click()
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.ID, id_reject_form)))
        reject_form = driver.find_element_by_id(id_reject_form)
        reject_form.find_element_by_css_selector(css_reject_text).send_keys('XXX')
        reject_form_confirm = driver.find_element_by_css_selector(css_reject_confirm)
        ActionChains(driver).move_to_element(reject_form_confirm.wrapped_element).click().perform()
        WebDriverWait(driver, T_60).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, css_loading_info)))
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_vm_status)))
        assert driver.find_element_by_css_selector(
            css_vm_status).text == 'Утверждена АР', 'ВМ не перешла в статус Утверждена АР'
        assert driver.find_element_by_css_selector(
            css_ipm_text).text == 'На доработке', 'ИПМ не перешел в статус На доработке'
    with allure.step("Выход из АС CF"):
        UIAuth(driver=driver).logout(auth=auth, driver=driver)
    with allure.step('Открыть вкладку ИПМ под ролью Кредитного специалиста'):
        step_authorization(auth, driver, login='credit_manager_login', passw=role + '_pass',
                           url_locator=url_reports[0],
                           title='Отчеты')
        driver.get(auth['protocol'] + auth['url'] + url_ipm_mv.format(NEW_MODEL, VM_ID))
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_ipm_statuses[0])))
        assert driver.find_element_by_css_selector(
            css_ipm_statuses[0]).text == 'На доработке', 'Статус ИПМ не соответствует ожидаемому'
    with allure.step('Нажать на замок'):
        WebDriverWait(driver, T_60).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_lock_vm))).click()
        WebDriverWait(driver, T_60).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_block_vm))).click()
        WebDriverWait(driver, T_60).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, css_panda)))
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.XPATH, xpath_text.format(' На согласовании '))))
        assert driver.find_element_by_css_selector(
            css_ipm_statuses[0]).text == 'На согласовании', 'Статус ИПМ не соответствует ожидаемому'
    with allure.step("Выход из АС CF"):
        UIAuth(driver=driver).logout(auth=auth, driver=driver)
    with allure.step('Открыть форму Модели под ролью Андеррайтера'):
        step_authorization(auth, driver, login='underwriter_login', passw=role + '_pass')
        driver.get(auth['protocol'] + auth['url'] + url_model_version.format(NEW_MODEL, VM_ID) + '&versionsPageIndex=2')
        WebDriverWait(driver, T_60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_ipm_form[0])))
        assert driver.find_element_by_css_selector(css_ipm_form[1]).get_attribute(
            "innerHTML") == 'На согласовании', 'Статус ИПМ на форме ВМ не соответствует ожидаемому'
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_dialog_window[0])))
        assert driver.find_element_by_css_selector(
            css_dialog_window[0]) is not None, 'Диалогове окно Согласование ИПМ отсутствует'
        driver.find_element_by_css_selector(css_dialog_window[1]).click()
        WebDriverWait(driver, T_60).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_ipm_approve)))
        ipm_approve = driver.find_element_by_css_selector(css_ipm_approve)
        ActionChains(driver).move_to_element(ipm_approve.wrapped_element).click().perform()
        WebDriverWait(driver, T_60).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, css_loading_info)))
        driver.get(auth['protocol'] + auth['url'] + url_model_version.format(NEW_MODEL, VM_ID) + '&versionsPageIndex=2')
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_ipm_form[1])))
        assert driver.find_element_by_css_selector(css_ipm_form[
                                                       1]).text == 'Ожидает подтверждения сделки', 'Статус ИПМ на форме ВМ не соответствует ожидаемому'
        TEST_PASSED[role] = 'IPM_APPROVED'


@pytest.mark.smoke_ui_test
@pytest.mark.ui_test
@flaky.flaky(max_runs=3)
@allure.testcase(url='http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/35368',
                 name='ИПМ. Подтверждение актуальности сделки')
@pytest.mark.parametrize("role", IPM_ACTUALITY_DEAL_ROLE)
def test_deal_actuality(auth, role, initial_driver):
    """Author: Макаренков Александр Валерьевич"""
    with allure.step("Выход из АС CF"):
        if TEST_PASSED['underwriter'] != 'IPM_APPROVED':
            pytest.skip(f"Тест test_deal_actuality -ИПМ. Подтверждение актуальности сделки для роли {role} не пройден")
        driver = initial_driver
        UIAuth(driver=driver).logout(auth=auth, driver=driver)
    with allure.step('Открыть вкладку ИПМ под ролью сотрудника мониторинга '):
        step_authorization(auth, driver, login=role + '_login', passw=role + '_pass',
                           url_locator=url_reports[0],
                           title='Отчеты')
        driver.get(auth['protocol'] + auth['url'] + url_ipm_mv.format(NEW_MODEL, VM_ID))
        WebDriverWait(driver, T_60).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, css_ipm_actuality[0])))
        WebDriverWait(driver, T_60).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_ipm_actuality[1])))
        deal_id = str(VM_ID) + str(NEW_MODEL)
        driver.find_element_by_css_selector(css_ipm_actuality[1]).send_keys(deal_id)
        driver.find_element_by_css_selector(css_ipm_actuality[2]).click()
        WebDriverWait(driver, T_60).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, css_panda)))
        assert driver.find_element_by_css_selector(
            css_actuality_status).text == 'Да ', 'Сделка не актуальна '
        deal_relevance = get_id(auth['cms'],
                                query=f"SELECT IS_DEAL_ACTIVE FROM IPMS WHERE DEAL_CRM_ID = '{deal_id}'")
        assert deal_relevance == '1', 'Признак актуальности не передался в БД'
