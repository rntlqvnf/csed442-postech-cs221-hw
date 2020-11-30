# grading.py
# ----------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).
# 
# To POSTECH CS442 student, as you see from the above comment, this assignment 
# comes from the berkeley. I'd like to appreciate their work. I change some code
# to correctly work in python3. If you have any question, please contact to Seonghyeon
# Lee (sh0416@postech.ac.kr).
"""Common code for autograders"""

import sys
import time
import json
import traceback
from collections import defaultdict, Counter

# code to handle timeouts
#
# FIXME
# NOTE: TimeoutFuncton is NOT reentrant.  Later timeouts will silently
# disable earlier timeouts.  Could be solved by maintaining a global list
# of active time outs.  Currently, questions which have test cases calling
# this have all student code so wrapped.
#
class TimeoutFunctionException(Exception):
    """Exception to raise on a timeout"""
    pass


class TimeoutFunction:
    def __init__(self, function, timeout):
        self.timeout = timeout
        self.function = function

    def handle_timeout(self, signum, frame):
        raise TimeoutFunctionException()

    def __call__(self, *args, **keyArgs):
        # Check the time taken after the method has returned,
        # and throw an exception then.
        startTime = time.time()
        result = self.function(*args, **keyArgs)
        timeElapsed = time.time() - startTime
        if timeElapsed >= self.timeout:
            self.handle_timeout(None, None)
        return result


class Grades:
    "A data structure for project grades, along with formatting code to display them"
    def __init__(self, projectName, questionsAndMaxesList,
                 gsOutput=False):
        """
        Defines the grading scheme for a project
        projectName: project name
        questionsAndMaxesDict: a list of (question name, max points per question)
        """
        self.questions = [el[0] for el in questionsAndMaxesList]
        self.maxes = dict(questionsAndMaxesList)
        self.points = Counter()
        self.messages = dict([(q, []) for q in self.questions])
        self.project = projectName
        self.start = time.localtime()[1:6]
        self.sane = True # Sanity checks
        self.currentQuestion = None # Which question we're grading
        self.gsOutput = gsOutput  # GradeScope output
        self.prereqs = defaultdict(set)

        print('Autograder transcript for %s' % self.project)
        print('Starting on %d-%d at %d:%02d:%02d' % self.start)

    def addPrereq(self, question, prereq):
        self.prereqs[question].add(prereq)

    def grade(self, gradingModule, exceptionMap = {}):
        """
        Grades each question
          gradingModule: the module with all the grading functions (pass in with sys.modules[__name__])
        """

        completedQuestions = set([])
        for q in self.questions:
            print('\nQuestion %s' % q)
            print('=' * (9 + len(q)), '\n')
            self.currentQuestion = q

            incompleted = self.prereqs[q].difference(completedQuestions)
            if len(incompleted) > 0:
                prereq = incompleted.pop()
                # NOTE: Make sure to complete Question `prereq` before working
                #       on Question `q`, because Question `q` builds upon
                #       your answer for Question `prereq`.
                continue

            try:
                # Call the question's function
                TimeoutFunction(getattr(gradingModule, q),1800)(self) 
            except Exception as inst:
                self.addExceptionMessage(q, inst, traceback)
                self.addErrorHints(exceptionMap, inst, q[1])
            except:
                self.fail('FAIL: Terminated with a string exception.')

            if self.points[q] >= self.maxes[q]:
                completedQuestions.add(q)

            print('\n### Question %s: %d/%d ###\n' % (q, self.points[q], self.maxes[q]))

        print('\nFinished at %d:%02d:%02d' % time.localtime()[3:6])
        print("\nProvisional grades\n==================")

        for q in self.questions:
            print('Question %s: %d/%d' % (q, self.points[q], self.maxes[q]))
            
        print('------------------')
        totalCount = sum(self.points.values())
        print('Total: %d/%d' % (totalCount, sum(self.maxes.values())))
        if totalCount == 25:
            print("""

                          ALL HAIL GRANDPAC.
                    LONG LIVE THE GHOSTBUSTING KING.

                        ---      ----      ---
                        |  \    /  + \    /  |
                        | + \--/      \--/ + |
                        |   +     +          |
                        | +     +        +   |
                      @@@@@@@@@@@@@@@@@@@@@@@@@@
                    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                  \   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                  \ /  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                    V   \   @@@@@@@@@@@@@@@@@@@@@@@@@@@@
                        \ /  @@@@@@@@@@@@@@@@@@@@@@@@@@
                          V     @@@@@@@@@@@@@@@@@@@@@@@@
                                  @@@@@@@@@@@@@@@@@@@@@@
                          /\      @@@@@@@@@@@@@@@@@@@@@@
                        /  \  @@@@@@@@@@@@@@@@@@@@@@@@@
                    /\  /    @@@@@@@@@@@@@@@@@@@@@@@@@@@
                  /  \ @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                  /    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                      @@@@@@@@@@@@@@@@@@@@@@@@@@
                          @@@@@@@@@@@@@@@@@@

              """)

        if self.gsOutput:
            self.produceGradeScopeOutput()

    def addExceptionMessage(self, q, inst, traceback):
        """
        Method to format the exception message, this is more complicated because
        we need to cgi.escape the traceback but wrap the exception in a <pre> tag
        """
        self.fail('FAIL: Exception raised: %s' % inst)
        self.addMessage('')
        for line in traceback.format_exc().split('\n'):
            self.addMessage(line)

    def addErrorHints(self, exceptionMap, errorInstance, questionNum):
        typeOf = str(type(errorInstance))
        questionName = 'q' + questionNum
        errorHint = ''

        # question specific error hints
        if exceptionMap.get(questionName):
            questionMap = exceptionMap.get(questionName)
            if (questionMap.get(typeOf)):
                errorHint = questionMap.get(typeOf)
        # fall back to general error messages if a question specific
        # one does not exist
        if (exceptionMap.get(typeOf)):
            errorHint = exceptionMap.get(typeOf)

        # dont include the HTML if we have no error hint
        if not errorHint:
            return ''

        for line in errorHint.split('\n'):
            self.addMessage(line)

    def produceGradeScopeOutput(self):
        out_dct = {}

        # total of entire submission
        total_possible = sum(self.maxes.values())
        total_score = sum(self.points.values())
        out_dct['score'] = total_score
        out_dct['max_score'] = total_possible
        out_dct['output'] = "Total score (%d / %d)" % (total_score, total_possible)

        # individual tests
        tests_out = []
        for name in self.questions:
            test_out = {}
            # test name
            test_out['name'] = name
            # test score
            test_out['score'] = self.points[name]
            test_out['max_score'] = self.maxes[name]
            # others
            is_correct = self.points[name] >= self.maxes[name]
            test_out['output'] = "  Question {num} ({points}/{max}) {correct}".format(
                num=(name[1] if len(name) == 2 else name),
                points=test_out['score'],
                max=test_out['max_score'],
                correct=('X' if not is_correct else ''),
            )
            test_out['tags'] = []
            tests_out.append(test_out)
        out_dct['tests'] = tests_out

        # file output
        with open('gradescope_response.json', 'w') as outfile:
            json.dump(out_dct, outfile)
        return

    def fail(self, message, raw=False):
        "Sets sanity check bit to false and outputs a message"
        self.sane = False
        self.assignZeroCredit()
        self.addMessage(message, raw)

    def assignZeroCredit(self):
        self.points[self.currentQuestion] = 0

    def addPoints(self, amt):
        self.points[self.currentQuestion] += amt

    def deductPoints(self, amt):
        self.points[self.currentQuestion] -= amt

    def assignFullCredit(self, message="", raw=False):
        self.points[self.currentQuestion] = self.maxes[self.currentQuestion]
        if message != "":
            self.addMessage(message, raw)

    def addMessage(self, message, raw=False):
        if not raw:
            # We assume raw messages, formatted for HTML, are printed separately
            print('*** ' + message)
        self.messages[self.currentQuestion].append(message)
