# Generator
Generator is a message consumer responsible for getting competition questions from database and publishing them
to Pub/Sub topics

## Main tasks
Start game: Start publishing questions when accepted start signal from controller 
Team resend: Resend questions for specific team triggered by leaderboard if missing questions are found

## Prerequisites
### Create topics for publishing messages
- START topic: For prevention of pulling error. Generator will publish 6 questions(which can be modified) for each team at first
- LAKE topic: Store all rest of questions. Each team will only get their questions by filtering through message attribute - team
### Create subscription to consume message
- GENERATOR: Accept trigger message from controller

### DB table
generator_status: table used to record generation status

## Note
Generator can be easily scaled depending on the number of teams and questions
```
kubectl scale deploy generator --replicas=30
```