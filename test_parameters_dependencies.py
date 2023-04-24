import pytest
import allure

from API_Tests.BasicMetod.authorization import globalauth
from API_Tests.BasicMetod.model import delete_model
from API_Tests.BasicMetod.version import waiting_service_results, dependent_parameters_out, delete_version_model
from API_Tests.Generator.create_model import create_model_with_random_values
from API_Tests.Generator.create_version import upload_version_to_certain_model
from Test_Data.API_variables_data import check_inputs, check_outputs


@pytest.fixture(scope='module', autouse=True)
def setup_module(auth):
    global NEW_MODEL
    global MODEL_NAME
    global VM_ID
    resp = globalauth(auth, login=auth['business_admin_login'], password=auth['business_admin_pass'])
    NEW_MODEL, MODEL_NAME = create_model_with_random_values(auth, 1)
    VM_ID = upload_version_to_certain_model(auth, resp, NEW_MODEL, 'Dependencies.xlsx')

    yield
    delete_version_model(auth, VM_ID, response=resp)
    delete_model(auth, NEW_MODEL, response=resp)


@pytest.mark.api_test
@pytest.mark.smoke_api_test
@pytest.mark.core_test
@allure.testcase(url='http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/21098',
                 name='25. Загрузка ВМ на новом движке анализа зависимостей')
def test_create_model_for_dependencies(auth):
    """Author:Макаренков Александр Валерьевич"""
    with allure.step(f"Проверка прохождения анализа зависимостей для {MODEL_NAME}"):
        state_id = waiting_service_results(auth, VM_ID, upload_time=auth['upload_time'], service_type=7)
        assert state_id == 4, f'Анализ зависимостей не прошел для ВМ {VM_ID}'
    with allure.step("Поиск зависимых параметров inputs"):
        dependent_params = dependent_parameters_out(auth, version_id=VM_ID)
    dependent_params_inputs = [*dependent_params]
    assert len(dependent_params_inputs) != 0, "Не нашлось зависимых параметров на листе Inputs"
    assert dependent_params_inputs.sort() == check_inputs.sort(), "Зависимые параметры на листе Inputs не совпадают с ожидаемыми"

    with allure.step("Поиск зависимых параметров Outputs"):
        assert dependent_params == check_outputs, "Зависимые параметры на листе Outputs не совпадают с ожидаемыми"
