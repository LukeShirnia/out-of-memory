pipeline {
  agent any
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
}