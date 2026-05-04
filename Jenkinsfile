pipeline {
    agent any
    environment {
        APP_URL     = "http://65.0.74.194:3000"
        IMAGE_NAME  = "shopease-selenium-tests"
        RESULTS_DIR = "${WORKSPACE}/test-results"
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
        stage('Build Docker Image') {
            steps {
                echo "Building Docker image..."
                sh "docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} ."
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
						-e BASE_URL=${APP_URL} \
						-v ${WORKSPACE}/test-results:/app/test-results \
						${IMAGE_NAME}:${BUILD_NUMBER} \
						pytest tests/ -v --junit-xml=/app/test-results/results.xml

					docker exec jenkins chown -R jenkins:jenkins /var/jenkins_home/workspace/shopease-tests-pipeline/test-results || true
				"""
			}
		}
        stage('Publish Results') {
            steps {
                echo "Publishing test results..."
                junit allowEmptyResults: true,
                      testResults: 'test-results/results.xml'
            }
        }
        stage('Cleanup Docker Image') {
            steps {
                sh "docker rmi ${IMAGE_NAME}:${BUILD_NUMBER} || true"
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
					to: 'saleha.yasir123@gmail.com',
                    body: """
                        <div style="font-family:Arial,sans-serif;max-width:600px;">
                          <h2 style="color:${statusColor};">
                            ${statusEmoji} ShopEase Selenium Test Report
                          </h2>
                          <p><b>Job:</b> ${env.JOB_NAME}</p>
                          <p><b>Build:</b> #${BUILD_NUMBER}</p>
                          <p><b>Status:</b> ${currentBuild.result}</p>
                          <p><b>App URL:</b> <a href="${APP_URL}">${APP_URL}</a></p>
                          <p><b>Duration:</b> ${currentBuild.durationString}</p>
                          <hr>
                          <p style="color:#6b7280;font-size:12px;">
                            This email was sent automatically by Jenkins.
                          </p>
                        </div>
                    """,
                    recipientProviders: [
                        [$class: 'RequesterRecipientProvider'],
                        [$class: 'CulpritsRecipientProvider'],
                        [$class: 'DevelopersRecipientProvider']
                    ]
                )
            }
        }
    }
}