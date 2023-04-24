import allure
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from Locators.basic_locators import *
from Test_Data.UI_variables_data import T_60, PU_GRAPH_NAMES
from UI_Tests.PU_Tests.PU_Simple_metods.Metods_pz import graph_check
from UI_Tests.UI_base import step_authorization


@pytest.mark.smoke_ui_test
@pytest.mark.pu_test
@pytest.mark.ui_test
@pytest.mark.parametrize("role", ['portfolio_emloyee'])
@allure.testcase(url='http://10.36.135.172/Ecosystem/CashflowTracker/_workitems/edit/34343',
                 name='Графический отчет. Проверка отображения графиков в графическом отчете')
def test_pu_graphic_report(auth, role, initial_driver):
    """Мониторинг. Проверка страницы
    Author: Макаренков Александр"""
    with allure.step('Открыть форму Портфель - Графический отчет по статистике сверки сделок с ПЗ'):
        driver = initial_driver
        step_authorization(auth, driver, login=role + '_login', passw=role + '_pass', url_locator=url_portfolio,
                           title='Портфель')
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_pu_graph_analysis)))
        WebDriverWait(driver, T_60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_pu_graph_analysis)))
        driver.find_element_by_css_selector(css_pu_graph_analysis).click()
        WebDriverWait(driver, T_60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_pu_graph_title)))
        pu_graph_title = driver.find_element_by_css_selector(css_pu_graph_title)
        assert pu_graph_title.text == 'Графический отчет по статистике сверки сделок с ПЗ', 'Заголовок вкладки Графический отчет по сделкам-неверный'
        WebDriverWait(driver, T_60).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, css_report_spinner)))
        all_graph_titles = driver.find_elements_by_css_selector(css_pu_all_graphs_titles)
        all_graph_titles = [i.text for i in all_graph_titles]
        assert all_graph_titles.sort() == PU_GRAPH_NAMES.sort(), 'Заголовки графиков не совпадают'
        all_graphs = driver.find_elements_by_css_selector(css_pu_all_graphs)
        min_width = [int(i.get_attribute("width")) for i in all_graphs]
        min_height = [int(i.get_attribute("height")) for i in all_graphs]
        excel_btn = driver.find_element_by_css_selector(css_pu_download_excelgraph)
        assert excel_btn.get_attribute("label") == 'Выгрузить отчёт в Excel', 'Отсутствует кнопка выгрузки в excel'
        pptx_btn = driver.find_element_by_css_selector(css_pu_download_pptxgraph)
        assert pptx_btn.get_attribute(
            "label") == 'Выгрузить отчёт в Power Point', 'Отсутствует кнопка выгрузки в Power Point'
        max_icons = driver.find_elements_by_css_selector(css_maximize_graphs)
        assert len(max_icons) == 4, 'На странице отсутствует одна или более кнопка увеличения графика'
    with allure.step('Проверить графики на вкладке'):
        for i in max_icons:
            graph_check(driver, i, min_width, min_height)
