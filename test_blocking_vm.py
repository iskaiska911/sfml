import pytest
import allure
import flaky
from selenium.common.exceptions import TimeoutException

from API_Tests.BasicMetod.BasicMetod import get_id
from API_Tests.BasicMetod.DB_queries import get_id_by_title
from API_Tests.BasicMetod.authorization import globalauth
from API_Tests.BasicMetod.basic_method import get_request
from API_Tests.BasicMetod.version import unblock_mv
from Locators.basic_locators import *
from API_Tests.Reports_Tests.Reports_Helpers.ipm import api_save_ipm
from Test_Data.UI_variables_data import T_60, BUTTON_IN_LEFT_MENU, BLOCKING_VM
from UI_Tests.UI_base import step_authorization
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


@pytest.fixture(scope='module', autouse=True)
def setup_module(auth):
    global VM_LIST
    VM_LIST = []
    yield
    with allure.step(f"Удаление ИПМ "):
        resp = globalauth(auth, login=auth[f'business_admin_login'], password=auth[f'business_admin_pass'])
        for vm in VM_LIST:
            ipm_id = get_id(auth['cms'], query=f"SELECT ID FROM IPMS WHERE MODEL_VERSION_ID={vm}")
            if ipm_id is not None:
                delete_ipm = get_request(auth, url_reports_delete_ipm.format(ipm_id), resp)
                assert delete_ipm, "ИПМ не удален"
    with allure.step(f"Разблокировка ВМ"):
        for vm in VM_LIST:
            blocking_option = get_id(auth['cms'], query=f"SELECT STATUS_ID FROM MODEL_VERSIONS WHERE ID={vm}")
            if blocking_option != 0:
                unblock = unblock_mv(auth, vm, resp)
                assert unblock.status_code == 200, 'Разблокировка модели не произошла'
                assert unblock.json()['Status'] == 0, 'Разблокировка модели не произошла'


@pytest.mark.smoke_ui_test
@pytest.mark.ui_test
@flaky.flaky(max_runs=2)
@pytest.mark.parametrize("role", ['credit_manager'])
@allure.testcase(url='http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/36223',
                 name='Блокировка ВМ с КНР/без')
def test_blocking_mv(auth, role, initial_driver):
    """Блокировка ВМ с КНР/без
       Author: Макаренков Александр Валерьевич"""
    with allure.step('Подготовка переменных'):
        new_model = get_id_by_title(auth, BLOCKING_VM['MODEL_NAME'], 'MODELS')
        vm_id1 = get_id_by_title(auth, BLOCKING_VM['VM_1'], 'MODEL_VERSIONS')
        vm_id2 = get_id_by_title(auth, BLOCKING_VM['VM_2'], 'MODEL_VERSIONS')
        resp = globalauth(auth, login=auth[f'business_admin_login'], password=auth[f'business_admin_pass'])
        VM_LIST.extend((vm_id1, vm_id2))
    with allure.step(f"Проверка отсутствия ИПМ у ВМ {vm_id2}"):
        ipm_id = get_id(auth['cms'], query=f"SELECT ID FROM IPMS WHERE MODEL_VERSION_ID={vm_id2}")
        if ipm_id is not None:
            delete_ipm = get_request(auth, url_reports_delete_ipm.format(ipm_id), resp)
            assert delete_ipm, "ИПМ не удален"
    with allure.step(f"Проверка статуса черновика у ВМ"):
        for vm in (vm_id1, vm_id2):
            blocking_option = get_id(auth['cms'], query=f"SELECT STATUS_ID FROM MODEL_VERSIONS WHERE ID={vm}")
            if blocking_option != 0:
                unblock = unblock_mv(auth, vm, resp)
                assert unblock.status_code == 200, 'Разблокировка модели не произошла'
                assert unblock.json()['Status'] == 0, 'Разблокировка модели не произошла'
    with allure.step('Открыть форму Отчеты'):
        driver = initial_driver
        step_authorization(auth, driver, login=role + '_login', passw=role + '_pass', url_locator=url_models,
                           title='Модели')
    with allure.step(f'Открыть ВМ {vm_id1} и заблокировать'):
        driver.get(auth['protocol'] + auth['url'] + url_model_version.format(new_model, vm_id1))
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.ID, id_button_block_vm)))
        driver.find_element_by_id(id_button_block_vm).click()
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_button_accept_block)))
        driver.find_element_by_css_selector(css_button_accept_block).click()
        WebDriverWait(driver, T_60).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, css_button_accept_block)))
        driver.get(auth['protocol'] + auth['url'] + url_model_version.format(new_model, vm_id1))
        try:
            WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_status_vm_blocked)))
        except TimeoutException:
            driver.get(auth['protocol'] + auth['url'] + url_model_version.format(new_model, vm_id1))
            WebDriverWait(driver, T_60).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, css_status_vm_blocked)))
        assert driver.find_element_by_css_selector(css_check_status).get_attribute(
            "innerHTML") == 'Заблокирована', f'ВМ {vm_id1} не получила статус Заблокирована'
    with allure.step(f'Открыть ВМ {vm_id2} и заблокировать'):
        driver.get(auth['protocol'] + auth['url'] + url_model_version.format(new_model, vm_id2))
        WebDriverWait(driver, T_60).until(EC.presence_of_element_located((By.ID, id_button_block_vm)))
        driver.find_element_by_id(id_button_block_vm).click()
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_modal_window)))
        assert driver.find_element_by_css_selector(css_modal_window).get_attribute(
            "innerHTML") == 'Перед тем как отправить CF-модель на согласование убедитесь, что ИПМ создан для данной версии модели.', 'В диалоговом окне тражено неверное сообщение'
        driver.find_element_by_css_selector(css_button_modal_window_ipm.format(1)).click()
        assert driver.find_element_by_css_selector(css_check_status).get_attribute(
            "innerHTML") == 'Черновик', f'ВМ {vm_id2} не находится в  статусе Черновик'
        driver.get(auth['protocol'] + auth['url'] + url_model_version.format(new_model, vm_id2))
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.ID, id_button_block_vm)))
        driver.find_element_by_id(id_button_block_vm).click()
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_modal_window)))
        driver.find_element_by_css_selector(css_button_modal_window_ipm.format(2)).click()
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, css_button_in_left_menu.format(BUTTON_IN_LEFT_MENU['ИПМ']))))
        assert driver.current_url == auth['protocol'] + auth['url'] + url_reports[5].format(new_model,
                                                                                            vm_id2) + '&ipmid=0', 'Форма создания ИПМ не была открыта'
    with allure.step(f'Создать ИПМ для ВМ {vm_id2}'):
        ipm = api_save_ipm(auth, resp, ipm_id="0", ipm_title=f'ИПМ_{vm_id2}',
                           model_version=BLOCKING_VM['VM_2'], ipm_status='Черновик',
                           scenario=BLOCKING_VM['scenario'], ipm_inputs=BLOCKING_VM['ipm_inputs'])
        assert ipm, "ИПМ не сохранен"
        assert ipm.json()["Status"] == 0, "ИПМ не сохранен"
    with allure.step(f'Заблокировать ВМ {vm_id2}'):
        driver.get(auth['protocol'] + auth['url'] + url_model_version.format(new_model, vm_id2))
        WebDriverWait(driver, T_60).until(EC.element_to_be_clickable((By.ID, id_button_block_vm)))
        driver.find_element_by_id(id_button_block_vm).click()
        WebDriverWait(driver, T_60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_button_accept_block)))
        driver.find_element_by_css_selector(css_button_accept_block).click()
        driver.get(auth['protocol'] + auth['url'] + url_model_version.format(new_model, vm_id2))
        try:
            WebDriverWait(driver, T_60).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, css_status_vm_blocked)))
        except TimeoutException:
            driver.get(auth['protocol'] + auth['url'] + url_model_version.format(new_model, vm_id2))
            WebDriverWait(driver, T_60).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, css_status_vm_blocked)))
        assert driver.find_element_by_css_selector(css_check_status).get_attribute(
            "innerHTML") == 'Заблокирована', f'ВМ {vm_id2} не находится в  статусе Заблокирована'
