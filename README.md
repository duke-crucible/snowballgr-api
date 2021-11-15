# SnowballGR API

## Project Description

Snowball Study is a Duke University Respondent-Driven Sampling for Respiratory Disease Surveillance research project (https://sites.duke.edu/snowball/). 
Based on this study, Duke Crucible team has worked on a general release that aims to be used in other types of infectious disease studies. The general release
is named `SnowballGR` and it contains [UI repo](https://github.com/duke-crucible/snowbalgr-ui.git) and [API repo](https://github.com/duke-crucible/snowbalgr-api.git). 

The API repo provides dockerized backend RESTful services support for SnowballGR application. It is written in Python, based on [Flask framework](https://flask.palletsprojects.com/) and [Mongo DB](https://www.mongodb.com/).

## Local Development

Local development environment is managed by [docker-compose](https://docs.docker.com/compose/). Details of the local app cluster are documented in the docker-compose.yml(docker-compose.yml) file itself.

### Environment variables

Before running this stack locally, the following environment variables must be set in a file called `.env`. There is `.env.example` file with some of these variables (non secret ones) set, you may copy it to `.env` file and fill in the secret ones. Note that you are not supoosed to add `.env` file to Github since it contains some sensitive/private account information.

* `SERVICE_APP_ENV`: indicate which env it is running, should be one of [`prod`, `dev`, `test`, `local`]
* `SERVICE_SESSION_KEY`: flask session key
* `SERVICE_MONGODB_URI`: connection string to Mongo DB
* `SERVICE_DB_NAME`: Mongo DB name
* `SERVICE_SENDGRID_API_KEY`: your SendGrid account api key
* `SERVICE_SENDGRID_INVITE_TEMPLATE`: your invitation email template id in SendGrid
* `SERVICE_SENDGRID_FROM_ADDRESS`: from which the invitation email will be sent
* `REACT_APP_UI_ROOT`: snowballgr frontend url, e.g. http://localhost:3000
* `SERVICE_COMMUNICATION_CONNECTION_STRING`: your azure SMS connection string
* `SERVICE_COMMUNICATION_PHONE_NUMBER`: your azure SMS phone number

### Install and Run

1. Clone the project repository
    ```bash
    git clone https://github.com/duke-crucible/snowballgr-api.git
    cd snowballgr-api
    ```

2. Set up the environment variables
    ```bash
    cp .env.example .env
    ```
    Add sensitive/private information to `.env` file.

3. Build and Run
    Make sure you have Docker installed and running on your local, use below docker-compose commands to build and run:

    ```bash
    docker-compose build
    docker-compose up
    ```
    On your browser, go to http://localhost:8000/api/healthcheck to verify SnowballGR backend is up.

4. Integrate with UI

    Now you have a running python Flask backend, follow [instructions](https://github.com/duke-crucible/snowballgr-ui#local-development) to start SnowballGR frontend at http://localhost:3000.

5. Shell into the container
    ```bash
    docker-compose exec app bash
    ```

As you edit code, the server will automatically reload to pick up your changes. Sometimes you might need to shut down the server and rebuild the Docker images, for example if you add a new dependency. You can do this with `docker-compose stop` followed by `docker-compose build` and then restart the server with `docker-compose up`.

### Manage Dependencies
This project uses [poetry](https://python-poetry.org/) for dependency management. Use `poetry add/remove` to add or remove a dependency. Note that after adding a dependency, you'll need to rebuild the Docker image to make the dependency available inside the container.

## CI/CD
CI/CD configuration is not included in this repo. You need to add your own CICD configuration.  


## Deployment
This project can be deployed to any cloud services, e.g. Azure, AWS. Below is a step-by-step guide to deploy snowballgr-api to Azure App Service from [Azure Portal](https://portal.azure.com), refer to [Azure Documents](https://docs.microsoft.com/en-us/azure/?product=featured) for more information on deployment to Azure.

1. First select your subscription under which you want Snowballgr application to run.
2. From left panel select Resource groups, then create a new resource group or select an existing one (e.g. Snowballgr-RG).
3. Create Mongo DB for Snowballgr application:
    - Click `+ Create` and select `Azure Cosmos DB`,  click `Review + Create`, if validation is successful, click `Create` button in the card for `Azure Cosmos DB API for MongoDB`
    - Enter account name (e.g. snowballgr-mongo) and location (e.g. East US), write down the account name for later use. The rest can be left as default or configure per your need.
    - Once deployment is completed, click `Go to resource`, under `Settings` in the left pane, click `Connection String`, copy/write down `USERNAME` and `PRIMARY CONNECTION STRING` for later use.
4. Create a Container Registry:
    - Go to Azure Portal home page and select the resource group created in step 2.
    - Click `+ Create`, select Containers from left pane then select Container Registry from right panel, and click `Create' button.
    - In the `Create container registry` page, fill in the `Registry name` (e.g. snowballgracr) and choose `Location` (e.g. East US). You may leave the rest as default or change per your need.
    - Click `Reivew + create` button. If validation passes, click `Create`.
    - Once deployment is completed, click `Go to resource` and then click `Update` to enable `Admin user`.
5. Build, tag and push docker image to acr, this can be done from your terminal or from IDE (e.g. VSCode). Below is an example of doing so from terminal, assuming the resource group created in step 2 is named `Snowballgr-RG` and the acr created in step 4 is named `snowballgracr`. 

    - Make sure you are using the correct subscription, you may use following command to set it to your subscription:
    ```bash
    az account set --subscription <subscription>
    ```
    - Run following commands from snowballgr-api directory:
    ```bash
    docker build . -t snowballgr-api:latest
    docker tag snowballgr-api:latest snowballgracr.azurecr.io/snowballgr-api:latest
    az account set --subscription <subscription id>
    az acr credential show --resource-group Snowballgr-RG --name snowballgracr
    docker login snowballgracr.azurecr.io --username <username>
    ```
    replace `username` with values from the output of previous command. When prompted, type in one of the passwords from the previous step. You should see `Login Succeeded` message, next push the image to the registry:
    ```bash
    docker push snowballgracr.azurecr.io/snowballgr-api:latest
    ```
    This may take some time in the first attempt. After push succeeds, go back to Azure portal, go to the acr (e.g. snowballgracr), under `Services` in the left pane, click `Repositories`, you should be able to find the image in the repository of snowballgr-api.
6. Deploy Snowballgr-API to Azure App Service
    - Repeat step 1 and select the resource group created in step 2
    - Click `+ Create` and select `Web App`
    - Enter basic information: Web App name (e.g. `snowballgr-api`), select Docker Container for Publish, select Linux as Operating System, select your region and your existing service plan or create a new one per your need, then go to Docker page
    - On Docker page, select Single Container and Azure Container Registry as Image Source, then select registry created in step 4, choose image to run, no need to provide startup command
    - Click `Review+create` button, review your settings then click `Create`
    - Once deployment is complete, click `Go to resource`. Select Configuration under Settings in left panel.
    - Click `+ New application setting` to set up the [Environment variables](#Environment-variables) mentioned above

        * `SERVICE_APP_ENV`: `prod` or `dev`
        * `SERVICE_SESSION_KEY`: flask session key, e.g. `notsecretdevkey`
        * `SERVICE_MONGODB_URI`: `PRIMARY CONNECTION STRING` from step 3
        * `SERVICE_DB_NAME`: db name which is same as `USERNAME` from step 3
        * `SERVICE_SENDGRID_API_KEY`: your SendGrid account api key
        * `SERVICE_SENDGRID_INVITE_TEMPLATE`: your invitation email template id in SendGrid
        * `SERVICE_SENDGRID_FROM_ADDRESS`: from which the invitation email will be sent
        * `REACT_APP_UI_ROOT`: snowballgr frontend url, e.g. https://snowballgr.azurewebsites.net
        * `SERVICE_COMMUNICATION_CONNECTION_STRING`: your azure SMS connection string
        * `SERVICE_COMMUNICATION_PHONE_NUMBER`: your azure SMS phone number

    - Save your configuration, this should trigger your web app restarted
    - Wait for 5 minutes, click `Overview` in the left pane, click `URL` of your backend (e.g. https://snowballgr-api.azurewebsites.net), attach `/api/healthcheck` to the URL, you should see some healthcheck message on the page.

