import time
from behave import then
from tests.steps.auth import check_dashboard_is_visible


@then("The dashboard shows the login button")
def step_impl(context):
    assert len(context.webdriver.find_elements_by_link_text("Login")) == 0


@then("The dashboard does not show the login button")
def step_impl(context):
    assert len(context.webdriver.find_elements_by_link_text("Login")) == 0


@then("The dashboard shows the instance as {state}")
def step_impl(context, state):
    context.webdriver.refresh()
    check_dashboard_is_visible(context)
    time.sleep(1)
    context.webdriver.find_element_by_class_name("search-input").clear()
    time.sleep(.1)
    context.webdriver.find_element_by_class_name("search-input").send_keys(context.instance_id)
    time.sleep(1)
    dash_rows = context.webdriver.find_elements_by_xpath('//*[@id="table"]/tbody/tr')
    assert len(dash_rows) == 1

    dash_state = dash_rows[0].find_element_by_xpath("./td[4]").text
    assert dash_state == state
