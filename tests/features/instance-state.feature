Feature: Instance State

Background:
  Given an approved user is signed in
  And an instance is created

Scenario: Authenticated User sees a running instance
  When the instance is started
  Then The API shows the instance as running
  And The dashboard shows the instance as running

Scenario: Authenticated User sees a stopped instance
  When the instance is stopped
  Then The API shows the instance as stopped
  And The dashboard shows the instance as stopped

Scenario: Authenticated User sees a terminated instance
  When the instance is terminated
  Then The API shows the instance as terminated
  And The dashboard shows the instance as terminated