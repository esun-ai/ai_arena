# Insert-task

Insert-task is a cronjob executed when the game starts

## Main flow
1. Send request to controller API: trigger controller to call generator for question generation
2. Start game: Send signals to trigger controller_sub to start working

## Note
In k8s, components can interact through the service name.
For example, you can send a request to Controller by using http://controller-svc.namespace/get_teams as URL
