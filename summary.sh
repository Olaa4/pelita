#!/bin/zsh

echo "Project summary / QA for pelita"
echo "----------------------------------------------------------------------"
echo "Lines of code:"
echo "  in pelita/                : "$( wc -l pelita/**/*.py | tail -1 | sed 's/total//')
echo "  in test/                  : "$( wc -l test/**/*.py | tail -1 | sed 's/total//')
echo "  in both                   : "$( wc -l {pelita,test}/**/*.py | tail -1 | sed 's/total//')
echo ""
echo "Running pylint... please stand by!"
pelita_score=$( pylint pelita/**/*.py &> /dev/null | tail -3 | \
     grep 'Your code' | sed 's/Your\ code\ has\ been\ rated at\ \([^ ]*\) .*$/\1/')
test_score=$( pylint test/**/*.py &> /dev/null | tail -3 | \
     grep 'Your code' | sed 's/Your\ code\ has\ been\ rated at\ \([^ ]*\) .*$/\1/')
both_score=$( pylint {pelita,test}/**/*.py &> /dev/null | tail -3 | \
     grep 'Your code' | sed 's/Your\ code\ has\ been\ rated at\ \([^ ]*\) .*$/\1/')
echo "Pylint score:"
echo "  for pelita/               : "$pelita_score
echo "  for test/                 : "$test_score
echo "  for both/                 : "$both_score
echo ""
echo "Running tests... please stand by!"
test_stats=$( nosetests --with-coverage --cover-package pelita 2>&1 >/dev/null)
echo "  Total number of tests     : "$( echo $test_stats | grep 'Ran' | sed 's/Ran\ \(.*\)\ tests.*/\1/' )
echo "  # assert statements       : "$( grep 'assert' -c test/**/*.py | sed 's/.*://' | \
     python -c "import sys; print sum(int(l) for l in sys.stdin)" )
echo "  Test coverage             : "$( echo $test_stats | grep 'TOTAL' |  sed 's/TOTAL.*\(......$\)/\1/')
echo "  Result                    : "$( echo $test_stats | tail -1)
