read -p "Heroku app name: " APP_NAME
#APP_NAME=nusummiteers
heroku container:login
heroku plugins:install heroku-config
heroku config:push -o --app $APP_NAME # -o overwites upstream -c deletes from upstream
heroku container:push bot --app $APP_NAME
heroku container:release bot --app $APP_NAME
echo "Successfully deployed!"
