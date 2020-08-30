heroku container:login
heroku plugins:install heroku-config
heroku config:push --app $APP_NAME
heroku container:push bot --app $APP_NAME
heroku container:release bot --app $APP_NAME
echo "Successfully deployed!"

