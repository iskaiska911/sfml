import pytest
import flaky
import allure
from selenium.common.exceptions import TimeoutException

from API_Tests.BasicMetod.BasicMetod import all_select
from API_Tests.BasicMetod.authorization import globalauth
from API_Tests.BasicMetod.basic_method import get_request
from UI_Tests.ReportsTests.ReportsHelpers.Reports_page import click_button_in_left_menu, select_model_and_vm_in_report, \
    waiting_mbp_request
from UI_Tests.UI_base import step_authorization
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Test_Data.UI_variables_data import T_60, LIST_ROLES_MBP, MBP_DATA, BUTTON_IN_LEFT_MENU, MBP_CONDITIONS
from Locators.basic_locators import *


@pytest.fixture(scope='module', autouse=True)
def setup_module(auth):
    global VM_ID, NEW_MODEL, MBP_ID_NEW
    MBP_ID_NEW = []
    VM_ID, NEW_MODEL = all_select(auth['cms'],
                                  query=f"select ID,MODEL_ID from MODEL_VERSIONS WHERE TITLE ='{MBP_DATA['VM']}'")[0]
    yield
    resp = globalauth(auth, login=auth[f'system_login'], password=auth[f'system_pass'])
    delete_new_mbp = get_request(auth, url_delete_mbp.format(MBP_ID_NEW[-1]), resp)
    assert delete_new_mbp.status_code == 200, 'Последний мбп не удален'

@pytest.mark.smoke_ui_test
@pytest.mark.ui_test
@flaky.flaky
@pytest.mark.parametrize("role", LIST_ROLES_MBP)
@allure.testcase(url='http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/42078',
                 name='МБП. Ручное создание')
def test_mbp_creation(auth, role, initial_driver):
    """Author: Макаренков Александр Валерьевич """
    with allure.step("Отчеты-МБП"):
        driver = initial_driver
        step_authorization(auth, driver, login=role + '_login', passw=role + '_pass',
                           url_locator=url_reports[0], title='Отчеты')
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, css_button_in_left_menu.format(BUTTON_IN_LEFT_MENU['МБП']))))
        click_button_in_left_menu(auth, driver, role, button_name='МБП')
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_choose_model_input)))
        select_model_and_vm_in_report(driver, MBP_DATA['MODEL_NAME'])
        try:
            WebDriverWait(driver, T_60).until(EC.visibility_of_any_elements_located((By.CSS_SELECTOR, css_mbp_list)))
        except TimeoutException:
            resp = globalauth(auth, login=auth[f'system_login'], password=auth[f'system_pass'])
            mbp_id, latest_mbp_date = all_select(auth['cms'],
                                                 query=f"select ID,CREATED from MBP_REQUESTS WHERE created=(SELECT max(Created) FROM MBP_REQUESTS where TITLE like '%{MBP_DATA['VM']}%')")[0]
            delete_mbp = get_request(auth, url_delete_mbp.format(mbp_id), resp)
            assert delete_mbp.status_code == 200, 'Последний мбп не удален'
            driver.get(auth['protocol'] + auth['url'] + url_mbp.format(NEW_MODEL, VM_ID))
            WebDriverWait(driver, T_60).until(EC.visibility_of_any_elements_located((By.CSS_SELECTOR, css_mbp_list)))
        assert [i.text for i in driver.find_elements_by_css_selector(
            css_mbp_list)] == MBP_CONDITIONS, f'Пункты чеклиста для ВМ {VM_ID} не соответствуют тест-кейсу'
        assert len(driver.find_elements_by_css_selector(css_green_ticks)) == len(driver.find_elements_by_css_selector(
            css_mbp_list)), f' Не все пункты чеклиста для ВМ {VM_ID} отмечены зелеными галками'
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_mbp_button)),
                                          message='Кнопка создания МБП не найдена').click()
    with allure.step("Создать мониторинг бизнес-плана"):
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_mbp_form)),
                                          message='Форма МБП не найдена')
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_mbp_status)))
        assert driver.find_element_by_css_selector(
            css_mbp_status).text == "На мониторинге", "МБП не перешел в статус На мониторинге"
        mbp_id_new, latest_mbp_date_new = all_select(auth['cms'],
                                                     query=f"select ID,CREATED from MBP_REQUESTS WHERE created=(SELECT max(Created) FROM MBP_REQUESTS where TITLE like '%{MBP_DATA['VM']}%')")[0]
        assert mbp_id_new == mbp_id + 1 and latest_mbp_date_new > latest_mbp_date, 'Запись в MBP_REQUESTS не была создана'
        MBP_ID_NEW.append(mbp_id_new)
    with allure.step("Убедиться, что расчет завершается без ошибок"):
        mbp_status = waiting_mbp_request(auth, mbp_id_new, auth['upload_time'])
        assert mbp_status == 2, 'Расчет MBP_REQUESTS завершился с ошибкой'
