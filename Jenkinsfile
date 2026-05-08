pipeline {
    agent any

    environment {
        BASE_URL = "http://localhost:3000"
        IMAGE_NAME = "shopease-tests"
    }

    triggers {
        githubPush()
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Cloning test repository..."
                git branch: 'main',
                    url: 'https://github.com/salehayasir/shopease-tests.git'
            }
        }

        stage('Build Test Image') {
            steps {
                echo "Building Docker image for Selenium tests..."
                sh "docker build -t ${IMAGE_NAME} ."
            }
        }

        stage('Test') {
            steps {
                echo "Running Selenium test cases..."
                sh """
                    mkdir -p \$(pwd)/reports
                    docker run --rm \
                        --network=host \
                        -e BASE_URL=${BASE_URL} \
                        -v \$(pwd)/reports:/app/reports \
                        ${IMAGE_NAME} \
                        pytest tests/test_shopease.py \
                            --html=reports/report.html \
                            --self-contained-html \
                            -v
                """
            }
            post {
                always {
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'reports',
                        reportFiles: 'report.html',
                        reportName: 'Selenium Test Report'
                    ])
                }
            }
        }
    }

    post {
        always {
            script {
                // Get the email of whoever triggered the push
                def pusherEmail = ''
                try {
                    pusherEmail = env.GIT_AUTHOR_EMAIL ?: sh(
                        script: "git log -1 --format='%ae'",
                        returnStdout: true
                    ).trim()
                } catch (Exception e) {
                    pusherEmail = 'qasimalik@gmail.com'
                }

                def buildStatus = currentBuild.currentResult ?: 'UNKNOWN'
                def statusEmoji = buildStatus == 'SUCCESS' ? '✅' : '❌'

                emailext(
                    to: "${pusherEmail}",
                    subject: "${statusEmoji} ShopEase Test Results — Build #${BUILD_NUMBER} — ${buildStatus}",
                    body: """
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2>${statusEmoji} ShopEase Selenium Test Results</h2>
    <table style="border-collapse: collapse; width: 100%;">
        <tr>
            <td style="padding: 8px; font-weight: bold;">Build Number:</td>
            <td style="padding: 8px;">#${BUILD_NUMBER}</td>
        </tr>
        <tr style="background:#f2f2f2;">
            <td style="padding: 8px; font-weight: bold;">Status:</td>
            <td style="padding: 8px;"><strong>${buildStatus}</strong></td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">Branch:</td>
            <td style="padding: 8px;">${GIT_BRANCH ?: 'main'}</td>
        </tr>
        <tr style="background:#f2f2f2;">
            <td style="padding: 8px; font-weight: bold;">Commit:</td>
            <td style="padding: 8px;">${GIT_COMMIT?.take(8) ?: 'N/A'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">Duration:</td>
            <td style="padding: 8px;">${currentBuild.durationString}</td>
        </tr>
        <tr style="background:#f2f2f2;">
            <td style="padding: 8px; font-weight: bold;">Jenkins URL:</td>
            <td style="padding: 8px;"><a href="${BUILD_URL}">${BUILD_URL}</a></td>
        </tr>
    </table>
    <br/>
    <p>📄 Full test report: <a href="${BUILD_URL}Selenium_20Test_20Report/">${BUILD_URL}Selenium_20Test_20Report/</a></p>
    <p style="color: gray; font-size: 12px;">This email was sent automatically by Jenkins CI for ShopEase.</p>
</body>
</html>
                    """,
                    mimeType: 'text/html',
                    attachmentsPattern: 'reports/report.html'
                )
            }
        }
    }
}
