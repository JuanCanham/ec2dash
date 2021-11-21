from behave import given, when, then


@given("no authentication")
def step_impl(_context):
    """Do nothing"""


@given("a user signs up")
def step_impl(context):
    context.webdriver.get(context.dashboard)
    context.webdriver.find_element_by_link_text("Login").click()
    context.webdriver.find_element_by_link_text("Sign up").click()
    context.webdriver.find_element_by_name("username").send_keys(context.user_name)
    context.webdriver.find_element_by_name("password").send_keys(context.password)
    context.webdriver.find_element_by_name("signUpButton").click()


@then("the user cannot sign in")
def step_impl(context):
    attempt_signin(context)
    assert any(
        (
            elem.is_displayed()
            for elem in context.webdriver.find_elements_by_id("loginErrorMessage")
        )
    )


@then("the user can sign in")
def step_impl(context):
    attempt_signin(context)
    assert context.webdriver.current_url.startswith(context.dashboard)
    for elem in context.webdriver.find_elements_by_link_text("Login"):
        assert not elem.is_displayed()


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
        (
            elem.is_displayed()
            for elem in context.webdriver.find_elements_by_link_text("Login")
        )
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
    else:
        for elem in context.webdriver.find_elements_by_id("signInFormUsername"):
            if elem.is_displayed():
                elem.send_keys(context.user_name)
        for elem in context.webdriver.find_elements_by_id("signInFormPassword"):
            if elem.is_displayed():
                elem.send_keys(context.password)
        click_visible_by_name(context, "signInSubmitButton")


@given("{provider} already has a clientId specified")
def step_impl(context, provider: str):
    context.clientIdExists = (
        len(get_stack_parameter(context, f"{provider}ClientId")) > 0
    )
    if not context.clientIdExists:
        print(f"No Client ID provided for {provider}\n")


def get_stack_parameter(context, key: str):
    describe_response = context.cloudformation.describe_stacks(
        StackName=context.main_stack_name
    )
    value = [
        param["ParameterValue"]
        for param in describe_response["Stacks"][0]["Parameters"]
        if param["ParameterKey"] == key
    ][0]
    return value


@when("A user can login using {provider} (or doesn't see it)")
def step_impl(context, provider: str):
    context.webdriver.get(context.dashboard)
    context.webdriver.find_element_by_link_text("Login").click()
    button_name = f"{provider.lower()}SignUpButton"
    if context.clientIdExists:
        click_visible_by_name(context, button_name)
    else:
        assert len(context.webdriver.find_elements_by_name(button_name)) == 0


@then("The provider login page should work (if it exists)")
def step_impl(context):
    if context.clientIdExists:
        assert (
            len(
                context.webdriver.find_elements_by_css_selector(
                    '[autocomplete="username"]'
                )
            )
            == 1
        )
        assert (
            context.webdriver.find_element_by_tag_name("body")
            .text.lower()
            .count("invalid")
            == 0
        )


def click_visible_by_name(context, query: str):
    for elem in context.webdriver.find_elements("name", query):
        if elem.is_displayed():
            elem.click()
