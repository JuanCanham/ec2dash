import time
from behave import given, when, then


@given("no authentication")
def step_impl(context):
    context.dashboard = f"https://{context.domain}/"


@given("a user signs up")
def step_impl(context):
    context.webdriver.get(context.dashboard)
    context.webdriver.find_element_by_link_text("Login").click()
    context.webdriver.find_element_by_link_text("Sign up").click()
    context.webdriver.find_element_by_name("username").send_keys(context.user_name)
    context.webdriver.find_element_by_name("password").send_keys(context.password)
    context.webdriver.find_element_by_name("signUpButton").click()
    time.sleep(2)


@then("the user cannot sign in")
def step_impl(context):
    attempt_signin(context)
    assert any(
        [
            e.is_displayed()
            for e in context.webdriver.find_elements_by_id("loginErrorMessage")
        ]
    )


@then("the user can sign in")
def step_impl(context):
    attempt_signin(context)
    assert context.webdriver.current_url.startswith(context.dashboard)
    assert all(
        [
            not e.is_displayed()
            for e in context.webdriver.find_elements_by_link_text("Login")
        ]
    )


@when("the user is approved")
def step_impl(context):
    context.cognito.admin_confirm_sign_up(
        UserPoolId=context.user_pool_id, Username=context.user_name
    )


@given("an approved user is signed in")
def step_impl(context):
    check_dashboard_is_visible(context)


def check_dashboard_is_visible(context):
    if not context.webdriver.current_url.startswith(context.dashboard) or any(
        [
            e.is_displayed()
            for e in context.webdriver.find_elements_by_link_text("Login")
        ]
    ):
        attempt_signin(context)


def attempt_signin(context):
    context.webdriver.get(context.dashboard)
    context.webdriver.find_element_by_link_text("Login").click()
    login_buttons = [
        btn
        for btn in context.webdriver.find_elements_by_class_name("btn-primary")
        if btn.is_displayed() and context.user_name in btn.text
    ]
    if login_buttons:
        login_buttons[0].click()
        return
    [
        e.send_keys(context.user_name)
        for e in context.webdriver.find_elements_by_id("signInFormUsername")
        if e.is_displayed()
    ]
    [
        e.send_keys(context.password)
        for e in context.webdriver.find_elements_by_id("signInFormPassword")
        if e.is_displayed()
    ]
    [
        e.click()
        for e in context.webdriver.find_elements_by_name("signInSubmitButton")
        if e.is_displayed()
    ]
