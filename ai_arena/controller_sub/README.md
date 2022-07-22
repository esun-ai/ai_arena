# Controller Sub
Controller Sub is a message consumer responsible for grabbing competition questions from LAKE(each team's subscription) or START 
and publishing to SEA(questions ready for launching)

## Main tasks (executed depends on message's attribute from controller topic)
- Start: Get questions from START and publish them to SEA
- Trigger next: Get questions from LAKE(each team's subscription) to SEA

## Prerequisites
### Create topics for publishing messages
- SEA topic: Questions ready for launching. Controller sub will put new question in when trigger_next message was accepted

### Create subscriptions to consume message
- CONTROLLER SUB: Accept start or trigger_next signal from Controller
- LAKE: Store all rest of the questions. Split by team_id
- START: Store 6 questions for each team.

## Note
Once the Controller Sub gets the trigger_next message, Controller Sub will move questions from LAKE to SEA