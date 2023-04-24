import pytest
import allure
import flaky
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from API_Tests.BasicMetod.BasicMetod import get_list
from API_Tests.BasicMetod.DB_queries import get_id_by_title
from Locators.basic_locators import *
from Test_Data.UI_variables_data import T_60, SEASONAL_MODEL
from UI_Tests.ReportsTests.ReportsHelpers.Reports_page import seasonal_ipm
from UI_Tests.UI_base import step_authorization


@flaky.flaky(max_runs=3)
@pytest.mark.smoke_test
@pytest.mark.smoke_ui_test
@pytest.mark.parametrize("role", ['credit_manager'])
@allure.testcase(url='http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/36221', name='ИПМ. Сезонность')
def test_ipm_seasons(auth, role, initial_driver):
    """ИПМ. Сезонность
       Author: Макаренков Александр Валерьевич"""
    with allure.step('Открыть форму Отчеты'):
        driver = initial_driver
        step_authorization(auth, driver, login=role + '_login', passw=role + '_pass', url_locator=url_reports[4],
                           title='ИПМ')
    with allure.step(f'Открыть форму ИПМ для разных ВМ'):
        model_id = get_id_by_title(auth, SEASONAL_MODEL, 'MODELS')
        vm_id_list = sorted(get_list(auth['cms'], query=f"select id from MODEL_VERSIONS where MODEL_ID={model_id}"))
        result_mv1 = seasonal_ipm(driver, auth, model_id, vm_id_list[0])
        assert result_mv1 == {'Debt Restructuring 1', 'DSCR (LTM)', 'Debt Restructuring 2',
                              'ISCR (LTM)'}, "Показатели таблицы не совпадают с ожидаемыми для ВМ {}".format(
            vm_id_list[0])
        result_mv2 = seasonal_ipm(driver, auth, model_id, vm_id_list[1])
        assert result_mv2 == {'Debt Restructuring 1', 'DSCR', 'Debt Restructuring 2',
                              'ISCR'}, "Показатели таблицы не совпадают с ожидаемыми для ВМ {}".format(vm_id_list[1])
        driver.get(auth['protocol'] + auth['url'] + url_reports[5].format(model_id, vm_id_list[2]))
        WebDriverWait(driver, T_60).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_broken_table)))
        driver.find_element_by_css_selector(
            css_broken_table).text == 'Невозможно создать ИПМ. Не найдены параметры: ISCR (LTM), DSCR (LTM)', "Результаты страницы не совпадают с ожидаемыми для ВМ {}".format(
            vm_id_list[2])
