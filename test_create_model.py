import os
import random
import allure
import pytest
from selenium.webdriver.support.select import Select

from API_Tests.BasicMetod.basic_method import api_create_client
from API_Tests.BasicMetod.model import delete_client
from API_Tests.BasicMetod.rolesSetting import auth_login_pas
from Locators.basic_locators import *
from Test_Data.UI_variables_data import AFFILATION, DEAL_TYPES, REPORTING_DATE, PREDICTION_STEP, T_20, T_60
from UI_Tests.UI_authorization import time
from UI_Tests.UI_base import check_exist_page, check_filter_emptiness, WebDriverWait, EC, By, Keys, positive_solo_input

# Test Variables
MODEL_NAME = 'Тестовая модель '+str(random.randint(1, 1000))


@pytest.fixture(scope='module', autouse=True)
def setup_module(auth):
    with allure.step("Создание клиента"):
        global CLIENT_NEW_NAME
        client_id, client_name, id_crm = api_create_client(auth)
        CLIENT_NEW_NAME = client_name
    yield
    with allure.step("Удаление клиента"):
        resp_1 = auth_login_pas(auth, login='cf-service-deploy', pas=auth['business_admin_pass'])[0]
        delete_client(auth, client_id=client_id, response=resp_1)


@pytest.mark.core_test
@pytest.mark.ui_test
@allure.testcase(url="http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/32579", name='Создание карточки модели')
def test_create_model(auth, initial_driver):
    """Проверка перехода на вкладку создания модели и заполнения полей
    Author Макаренков Александр"""
    driver = initial_driver
    with allure.step('Открыть форму для добавления клиентов'):
        check_exist_page(auth, driver, f'input[name="{locator_client_by["title"]}"]', block_name='КЛИЕНТЫ', locator_button_add=locator_block_button_add['КЛИЕНТЫ'])
    with allure.step(f'В поиске клиента по названию ввести значение, {CLIENT_NEW_NAME}'):
        check_filter_emptiness(driver, locator_client_by)
        positive_solo_input(driver, locator_client_by['title'],CLIENT_NEW_NAME)
        WebDriverWait(driver, T_20).until(EC.invisibility_of_element((By.CSS_SELECTOR, css_loading_updating_block)))
        driver.find_element_by_css_selector(css_models_checkbox).click()
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_save_element)))
        driver.find_element_by_css_selector(css_save_element).click()
        WebDriverWait(driver, T_20).until_not(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_added_block)))
        client_check = driver.find_element_by_css_selector('[class="grid-col-ellipsis td_1"]').get_attribute('title')
        assert CLIENT_NEW_NAME in client_check, "Клиента не удалось добавить в карточку модели"
    with allure.step('Проверить можно ли выбрать групповую модель'):
        group_list = Select(driver.find_element_by_css_selector(css_by_companygroup))
        group_list.select_by_visible_text('Да')
        time.sleep(1)
    with allure.step(f'Ввести название модели {MODEL_NAME}'):
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, locator_block_button_add['НАЗВАНИЕ ГРУППЫ КОМПАНИЙ'])))
        client_name = driver.find_element_by_css_selector(locator_block_button_add['НАЗВАНИЕ ГРУППЫ КОМПАНИЙ'])
        client_name.send_keys(MODEL_NAME, Keys.ENTER)
        WebDriverWait(driver, T_20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, locator_block_button_add['НАЗВАНИЕ ГРУППЫ КОМПАНИЙ'])))
    with allure.step(f'Выбрать отраслевую принадлежность {AFFILATION["SEARCH_INDUSTRY"]}'):
        driver.find_element_by_css_selector(locator_block_button_add['ОТРАСЛЕВАЯ ПРИНАДЛЕЖНОСТЬ']).click()
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_sector_classifier_in_block)))
        sector_name = driver.find_element_by_css_selector(css_sector_classifier_in_block)
        sector_name.send_keys(AFFILATION['SEARCH_INDUSTRY'], Keys.ENTER)
        WebDriverWait(driver, T_20).until(EC.invisibility_of_element((By.CSS_SELECTOR, css_loading_updating_block)))
        driver.find_element_by_css_selector(css_models_checkbox).click()
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_save_element)))
        driver.find_element_by_css_selector(css_save_element).click()
        WebDriverWait(driver, T_20).until_not(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_added_block)))
        check_sector = driver.find_element_by_css_selector("[title~='"+AFFILATION['SEARCH_INDUSTRY']+"']").get_attribute('title')
        assert AFFILATION['SEARCH_INDUSTRY'] in check_sector, "Отраслевую принадлежность не удалось добавить в модель"
    with allure.step(f'Выбрать тип сделки {DEAL_TYPES["DEFAULT_DEAL"]}'):
        deals_list = Select(driver.find_element_by_css_selector(locator_block_button_add['ТИП СДЕЛКИ']))
        deals_list.select_by_visible_text(DEAL_TYPES['DEFAULT_DEAL'])
        check_deal_type = deals_list.first_selected_option
        assert check_deal_type.text == DEAL_TYPES['DEFAULT_DEAL'], "Выбор типа сделки не осуществлен"
    with allure.step('Выбрать ГОСБ'):
        driver.find_element_by_css_selector(locator_block_button_add['НАЗВАНИЕ БАНКА']).click()
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_headoffice_title)))
        driver.find_elements_by_css_selector(css_models_checkbox)[0].click()
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_save_element)))
        driver.find_element_by_css_selector(css_save_element).click()
        WebDriverWait(driver, T_20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_headoffice_title_on_card)))
        head_office_check = driver.find_elements_by_css_selector(css_headoffice_title_on_card)
        assert len(head_office_check) == 1, "ГОСБ не удалось добавить в модель"
    with allure.step('Выбрать команду структураторов'):
        driver.find_element_by_css_selector(locator_block_button_add['ВЛАДЕЛЬЦЫ МОДЕЛИ']).click()
        WebDriverWait(driver, T_20).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, css_loading_block_content)))
        driver.find_elements_by_css_selector(css_models_checkbox)[0].click()
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_save_element)))
        driver.find_element_by_css_selector(css_save_element).click()
        WebDriverWait(driver, T_20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_model_owners_in_model_name)))
        structurers_check = driver.find_elements_by_css_selector(css_model_owners_in_model_name)
        assert len(structurers_check) > 0, "Не удалось заполнить команду структураторов"
    with allure.step('Выбрать команду проекта'):
        driver.find_element_by_css_selector(locator_block_button_add['РАЗРЕШЕН ДОСТУП']).click()
        WebDriverWait(driver, T_20).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, css_loading_block_content)))
        driver.find_elements_by_css_selector(css_models_checkbox)[0].click()
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_save_element)))
        driver.find_element_by_css_selector(css_save_element).click()
        WebDriverWait(driver, T_20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_model_users_in_model_name)))
        teamuser_check = driver.find_elements_by_css_selector(css_model_users_in_model_name)
        assert len(teamuser_check) > 0, "Не удалось заполнить команду проекта"
    with allure.step('Сохранить карточку модели'):
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.ID, id_button_save_model)))
        driver.find_element_by_id(id_button_save_model).click()
        dynamic_locator = "td[title='Группа_"+MODEL_NAME+"']"
        WebDriverWait(driver, T_60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, dynamic_locator)))
        search_model = driver.find_element_by_css_selector(dynamic_locator)
        assert search_model.text == "Группа_"+MODEL_NAME, "Не удалось создать модель"


@pytest.mark.core_test
@pytest.mark.ui_test
@allure.testcase(url="http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/32589", name='Загрузка версии модели')
def test_upload_version(auth, initial_driver):
    """Загрузка версии модели
    Author Макаренков Александр"""
    driver = initial_driver
    with allure.step('Загружаем ВМ'):
        dynamic_locator = "td[title='Группа_"+MODEL_NAME+"']"
        driver.find_element_by_css_selector(dynamic_locator).click()
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.ID, id_upload_version)))
        driver.find_element_by_id(id_upload_version).click()
        WebDriverWait(driver, T_20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_calendar)))
        calendar = driver.find_element_by_css_selector(css_calendar)
        calendar.click()
        calendar.send_keys(Keys.CONTROL, 'a', Keys.DELETE)
        calendar.send_keys(REPORTING_DATE['DEFAULT_DATE'], Keys.ENTER)
        prediction_step = Select(driver.find_element_by_css_selector(css_prediction_step))
        prediction_step.select_by_visible_text(PREDICTION_STEP['QUARTER'])
        driver.find_element_by_css_selector(css_disabledvalidation).click()
        upload_file = driver.find_element_by_css_selector(css_select_file)
        directory = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "..", "..", "..", "xlsFiles", f"{auth['file']}"))
        upload_file.send_keys(directory)
        WebDriverWait(driver, T_20).until(EC.invisibility_of_element((By.CSS_SELECTOR, css_uploading_bar)))
        driver.find_element_by_id(id_save_version).click()
        WebDriverWait(driver, T_60).until(EC.invisibility_of_element((By.CSS_SELECTOR, css_uploading_bar)))
        WebDriverWait(driver, T_20).until(EC.presence_of_element_located((By.ID, id_version_details)))
        assert MODEL_NAME.upper() in driver.find_element_by_css_selector(css_version_title).text, 'Не удалось загрузить версию модели'
    # Передача статуса загруженной ВМ
    with allure.step('Проверить статус версиии модели'):
        def waiting_version_upload():
            upload_time = 120
            time.sleep(60)
            timeout = time.time() + int(upload_time) * 60
            status = 'Загрузка'
            while timeout > time.time() and status == 'Загрузка':
                driver.refresh()
                WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_check_status)))
                check_status = driver.find_element_by_css_selector(css_check_status).text
                status = check_status
                time.sleep(30)
            return status
        get_version_model_status = waiting_version_upload()
        assert get_version_model_status in ('Загрузка не удалась', 'Черновик', 'Загружено с ошибкой'), 'VERSION NOT CALCULATION'


@pytest.mark.core_test
@pytest.mark.ui_test
@allure.testcase(url="http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/32591", name='Удаление версии модели:')
def test_delete_version(auth, initial_driver):
    """Удаление версии модели
    Author Макаренков Александр"""
    driver = initial_driver
    with allure.step('Удалить ВМ'):
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.ID, id_modelversion_edit)))
        driver.find_element_by_id(id_modelversion_edit).click()
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.ID, id_delete_version)))
        driver.find_element_by_id(id_delete_version).click()
        WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_confirm_delete)))
        driver.find_element_by_css_selector(css_confirm_delete).click()
        WebDriverWait(driver, T_20).until(EC.invisibility_of_element_located((By.ID, id_version_form)))
        versions = driver.find_elements_by_css_selector(css_uploaded_versions)
        assert len(versions) == 0, "Не удалось удалить версию модели"


@pytest.mark.core_test
@pytest.mark.ui_test
@allure.testcase(url="http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/32596", name='Удалить карточку модели:')
def test_delete_model(auth, initial_driver):
    """Удалить карточку модели
    Author Макаренков Александр"""
    driver = initial_driver
    with allure.step('Удалить карточку модели'):
        driver.refresh()
        WebDriverWait(driver, T_20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_model_header)))
        model_title = driver.find_element_by_css_selector(css_model_header).text
        if model_title == "ГРУППА_"+MODEL_NAME.upper():
            WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.ID, id_edit_model)))
            driver.find_element_by_id(id_edit_model).click()
            WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.ID, id_button_delete_model)))
            driver.find_element_by_id(id_button_delete_model).click()
            WebDriverWait(driver, T_20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_confirm_delete)))
            driver.find_element_by_css_selector(css_confirm_delete).click()
            WebDriverWait(driver, T_60).until(EC.invisibility_of_element_located((By.CLASS_NAME, class_loading_after_delete)))
            WebDriverWait(driver, T_20).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, css_loading_updating_block)))
            uploaded_models = driver.find_elements_by_css_selector(css_models_list_one)
            last_uploaded_model = uploaded_models[0].text
            assert last_uploaded_model != "Группа_"+MODEL_NAME, "Не удалось удалить модель"
