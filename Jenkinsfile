pipeline {
    agent any

    environment {
        // ── Change these two values to match your setup ──────────────────
        APP_URL      = "http://65.0.74.194:3000"   // ShopEase live URL
        TEST_REPO    = "https://github.com/salehayasir/shopease-tests.git"
        // ─────────────────────────────────────────────────────────────────
        IMAGE_NAME   = "shopease-selenium-tests"
        RESULTS_DIR  = "${WORKSPACE}/test-results"
    }

    triggers {
        // Triggered automatically by GitHub webhook on every push
        githubPush()
    }

    stages {

        stage('Checkout Test Code') {
            steps {
                echo "Cloning ShopEase test repository..."
                git branch: 'main', url: "${TEST_REPO}"
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image with Chrome + Selenium..."
                sh "docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} ."
            }
        }

        stage('Run Selenium Tests') {
            steps {
                echo "Running 20 Selenium test cases against ${APP_URL} ..."
                sh """
                    mkdir -p ${RESULTS_DIR}
                    docker run --rm \
                        --name shopease-tests-${BUILD_NUMBER} \
                        -e BASE_URL=${APP_URL} \
                        -v ${RESULTS_DIR}:/app/test-results \
                        ${IMAGE_NAME}:${BUILD_NUMBER}
                """
            }
            post {
                always {
                    // Publish JUnit results in Jenkins UI
                    junit allowEmptyResults: true,
                          testResults: 'test-results/results.xml'
                }
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
                // Build a readable test summary for the email body
                def testSummary = ""
                try {
                    def summary = junit testResults: 'test-results/results.xml'
                    testSummary = """
                        <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
                          <tr style='background:#f3f4f6;'>
                            <th>Total</th><th>Passed</th><th>Failed</th><th>Skipped</th>
                          </tr>
                          <tr>
                            <td>${summary.totalCount}</td>
                            <td style='color:green;'>${summary.passCount}</td>
                            <td style='color:red;'>${summary.failCount}</td>
                            <td>${summary.skipCount}</td>
                          </tr>
                        </table>
                    """
                } catch (e) {
                    testSummary = "<p>Could not parse test results.</p>"
                }

                def statusColor = currentBuild.result == 'SUCCESS' ? '#16a34a' : '#dc2626'
                def statusEmoji = currentBuild.result == 'SUCCESS' ? '✅' : '❌'

                emailext(
                    subject: "${statusEmoji} ShopEase Tests — ${currentBuild.result} [Build #${BUILD_NUMBER}]",
                    mimeType: 'text/html',
                    body: """
                        <div style="font-family:Arial,sans-serif;max-width:600px;">
                          <h2 style="color:${statusColor};">
                            ${statusEmoji} ShopEase Selenium Test Report
                          </h2>

                          <table border='0' cellpadding='4' style='margin-bottom:12px;'>
                            <tr><td><b>Job</b></td><td>${env.JOB_NAME}</td></tr>
                            <tr><td><b>Build</b></td><td>#${BUILD_NUMBER}</td></tr>
                            <tr><td><b>Status</b></td>
                                <td style='color:${statusColor};'><b>${currentBuild.result}</b></td></tr>
                            <tr><td><b>Triggered by</b></td>
                                <td>${currentBuild.getBuildCauses()[0]?.shortDescription ?: 'Unknown'}</td></tr>
                            <tr><td><b>App URL</b></td>
                                <td><a href='${APP_URL}'>${APP_URL}</a></td></tr>
                            <tr><td><b>Duration</b></td>
                                <td>${currentBuild.durationString}</td></tr>
                          </table>

                          <h3>Test Results</h3>
                          ${testSummary}

                          <br>
                          <a href="${env.BUILD_URL}testReport"
                             style="background:#2563eb;color:#fff;padding:8px 16px;
                                    border-radius:4px;text-decoration:none;">
                            View Full Report in Jenkins
                          </a>

                          <hr style="margin-top:24px;">
                          <p style="color:#6b7280;font-size:12px;">
                            This email was sent automatically by Jenkins.<br>
                            ShopEase DevOps Pipeline — COMSATS University
                          </p>
                        </div>
                    """,
                    // Email is sent to whoever pushed (triggers the build)
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
