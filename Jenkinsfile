pipeline {
  agent {
    docker {
      image 'python:2.7'
      args '-v /var/cache/pip/2.7:/var/cache/pip/2.7'
    }

  }
  stages {
    stage('pylint') {
      parallel {
        stage('pylint') {
          steps {
            sh 'pylint --rcfile=pylint.cfg oom_analyzer.py -j 4 -f parseable -r n'
          }
        }

        stage('Pycodestyle') {
          steps {
            sh 'pycodestyle oom_analyzer.py'
          }
        }

      }
    }

  }
  environment {
    PIP_DOWNLOAD_CACHE = '/var/cache/pip/2.7'
  }
}