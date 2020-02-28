pipeline {
  agent {
    docker {
      image 'python:2.7'
      args '-v /var/cache/pip/2.7:/var/cache/pip/2.7'
    }

  }
  stages {
    stage('Setup Tests') {
      steps {
        echo 'Installing Requirements...'
        sh '''pip install --cache-dir=/var/cache/pip/2.7 -U pip
'''
        sh 'pip install --cache-dir=/var/cache/pip/2.7 -r "tests/requirements.txt"'
      }
    }

    stage('oom-Analyzer Tests') {
      parallel {
        stage('oom-Analyzer Tests') {
          steps {
            echo 'Running PyTest'
            sh '''pytest --cov oom_analyzer --cov-report xml:cobertura.xml --cov-report term-missing --junitxml oom_analyzer.xml
'''
          }
        }

        stage('error') {
          steps {
            echo 'Running Pylint on '
            sh '''pylint --rcfile=pylint.cfg oom_analyzer.py -j 4 -f parseable -r n
'''
          }
        }

      }
    }

  }
}