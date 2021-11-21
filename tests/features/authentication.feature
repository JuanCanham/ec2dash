Feature: Authentication

Scenario: Unauthenticated API calls
  Given no authentication
  Then API returns an authentication error
  And The dashboard redirects to a login page within 5s

Scenario Outline: Oauth Login Providers work
   Given <provider> already has a clientId specified
   When A user can login using <provider> (or doesn't see it)
   Then The provider login page should work (if it exists)

 Examples: Providers
   | provider |
   | Google   |
   | Facebook |

Scenario: Unapproved User
  Given a user signs up
  Then the user cannot sign in

Scenario: Approved User
  When the user is approved
  Then the user can sign in
  And API returns an valid data
  And The dashboard does not show the login button