import time
from behave import then
from tests.steps.auth import check_dashboard_is_visible


@then("The dashboard does not show the login button")
def step_impl(context):
    assert len(context.webdriver.find_elements_by_link_text("Login")) == 0
    assert context.webdriver.current_url.startswith(context.dashboard)


@then("The dashboard shows the instance as {state}")
def step_impl(context, state: str):
    context.webdriver.refresh()
    check_dashboard_is_visible(context)
    context.webdriver.find_element_by_class_name("search-input").clear()
    context.webdriver.find_element_by_class_name("search-input").send_keys(
        context.instance_id
    )
    time.sleep(1)
    dash_rows = context.webdriver.find_elements_by_xpath('//*[@id="table"]/tbody/tr')
    assert len(dash_rows) == 1

    dash_state = dash_rows[0].find_element_by_xpath("./td[4]").text
    assert dash_state == state


@then("The dashboard redirects to a login page within {timeout}s")
def step_impl(context, timeout: str):
    context.webdriver.get(context.dashboard)
    time.sleep(int(timeout))
    assert not context.webdriver.current_url.startswith(context.dashboard)
    for url_part in [
        f"redirect_uri={context.dashboard}",
        "login",
        "response_type=token",
        "client_id",
    ]:
        assert context.webdriver.current_url.count(url_part)
