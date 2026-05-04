pipeline {
    agent any

    environment {
        APP_URL    = "http://65.0.74.194:3000"
        IMAGE_NAME = "shopease-selenium-tests"
        APP_IMAGE  = "shopease-app"
    }

    triggers {
        githubPush()
    }

    stages {

        stage('Checkout Code') {
            steps {
                echo "Using Jenkins auto checkout (SCM)..."
                checkout scm
            }
        }

        stage('Build Docker Image (Tests)') {
            steps {
                echo "Building test Docker image..."
                sh "docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} ."
            }
        }

        // 🔥 NEW REQUIRED STAGE (THIS IS WHAT YOUR PROFESSOR WANTS)
        stage('Deploy App') {
            steps {
                echo "Deploying application container..."
                sh """
                    docker stop shopease-app || true
                    docker rm shopease-app || true

                    docker build -t ${APP_IMAGE} .

                    docker run -d -p 3000:3000 --name shopease-app ${APP_IMAGE}
                """
            }
        }

        stage('Run Selenium Tests') {
            steps {
                echo "Running Selenium tests against ${APP_URL} ..."
                sh """
                    rm -rf ${WORKSPACE}/test-results
                    mkdir -p ${WORKSPACE}/test-results

                    docker run --rm \
                        --name shopease-tests-${BUILD_NUMBER} \
                        -v ${WORKSPACE}/test-results:/app/test-results \
                        -e BASE_URL=${APP_URL} \
                        ${IMAGE_NAME}:${BUILD_NUMBER} \
                        pytest tests/ -v --junit-xml=/app/test-results/results.xml
                """
            }
        }

        stage('Publish Results') {
            steps {
                echo "Publishing test results..."
                junit allowEmptyResults: false,
                      testResults: 'test-results/results.xml'
            }
        }

        stage('Cleanup Docker Images') {
            steps {
                sh """
                    docker rmi ${IMAGE_NAME}:${BUILD_NUMBER} || true
                    docker rmi ${APP_IMAGE} || true
                """
            }
        }
    }

    post {
        always {
            script {
                def statusColor = currentBuild.result == 'SUCCESS' ? '#16a34a' : '#dc2626'
                def statusEmoji = currentBuild.result == 'SUCCESS' ? '✅' : '❌'

                emailext(
                    subject: "${statusEmoji} ShopEase Tests — ${currentBuild.result} [Build #${BUILD_NUMBER}]",
                    mimeType: 'text/html',
                    to: 'qasimalik@gmail.com',
                    body: """
                        <div style="font-family:Arial,sans-serif;max-width:600px;">
                          <h2 style="color:${statusColor};">
                            ${statusEmoji} ShopEase CI/CD Test Report
                          </h2>

                          <p><b>Job:</b> ${env.JOB_NAME}</p>
                          <p><b>Build:</b> #${BUILD_NUMBER}</p>
                          <p><b>Status:</b> ${currentBuild.result}</p>
                          <p><b>App URL:</b> <a href="${APP_URL}">${APP_URL}</a></p>
                          <p><b>Duration:</b> ${currentBuild.durationString}</p>

                          <hr>
                          <p style="color:#6b7280;font-size:12px;">
                            Automated report from Jenkins CI/CD pipeline.
                          </p>
                        </div>
                    """,
                    recipientProviders: [
                        [$class: 'RequesterRecipientProvider']
                    ]
                )
            }
        }
    }
}