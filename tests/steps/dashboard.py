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
    dash_rows = [
        row
        for row in context.webdriver.find_elements_by_xpath(
            '//tbody[@id="dataTbody"]/tr'
        )
        if context.instance_id in row.text
    ]

    dash_state = dash_rows[0].find_element_by_xpath("./td[3]").text
    print("states", context.instance_id, state, dash_state)
    assert dash_state == state
