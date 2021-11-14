Feature: Authentication

Scenario: Unauthenticated API calls
  Given no authentication
  Then API returns an authentication error
  And The dashboard shows the login button

Scenario: Unapproved User
  Given a user signs up
  Then the user cannot sign in

Scenario: Approved User
  When the user is approved
  Then the user can sign in
  And API returns an valid data
  And The dashboard does not show the login button