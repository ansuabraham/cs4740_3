#!/usr/bin/env python
import os, os.path
import nltk
import pairing
from nltk.corpus import senseval
from optparse import OptionParser

CUTOFF_PROB = .5
BOOTSTRAP_CUTOFF_PROB = .8
# NOTE: Do not bootstrap (i.e., reps = 0) unless probabilities are on!
BOOTSTRAP_REPS = 5

USE_PROBS = False
USE_COLOCATION = False
USE_COOCCURRENCE = False
USE_BASE_WORD = False

CLASSIFIER=nltk.NaiveBayesClassifier
#CLASSIFIER=nltk.DecisionTreeClassifier #does not provide a probability measure
#CLASSIFIER=nltk.MaxentClassifier #much slower, prints lots of crap

def assign_features(instance):
	context = instance['context']
	pos = instance['position']
	d={}
	d['prev_word']=context[pos-1]
	d['actual_word']=context[pos]
	d['next_word']=context[pos+1]
	return d

def build_train(instances):
	"""Builds training instances from instances tagged with senses"""
	train=[]
	for instance in instances:
		d = assign_features(instance)
		instance_senses = instance['senses']
		for sense in instance_senses:
			pair = (d,sense)
			train.append(pair)
	return train

def build_test(instances):
	"""Builds test instances from instances tagged with or without senses"""
	test=[]
	for instance in instances:
		d = assign_features(instance)
		test.append(d)
	return test

def classify(train,test):
	classifier = CLASSIFIER.train(train)
	rawSenseList = classifier.batch_classify(test)
	probDistList = classifier.batch_prob_classify(test) if USE_PROBS\
		else [-1 for x in rawSenseList] #just a placeholder, should not be read
	return\
		[dict(sense=sense,prob=prob.prob(sense) if USE_PROBS else 1)\
		for sense,prob in zip(rawSenseList, probDistList)]

def bootstrap(train, test, classified):
	"""Bootstraps the classified test data onto the training
	train: list of (feature_dict, sense) pairs
	test:  list of (feature_dict)
	classified: list of (sense,prob) pairs matching up with test

	returns: a list of (feature_dict, sense) pairs containing all of train, with
	possibly more appended to it
	"""
	for result,test_inst in zip(classified, test):
		if result['prob'] > BOOTSTRAP_CUTOFF_PROB\
				and (test_inst, result['sense']) not in train:
			train.append((test_inst, result['sense']))
	return train

def batch_classify(items, tests):
	senses = []
	for item in items:
		lexitem = ".".join(item.split(".")[0:2])
		trains=\
			[dict(context=instance.context,\
				position=instance.position,\
				senses=instance.senses)\
			for instance in senseval.instances(item)]
		train=build_train(trains)
		test=build_test(tests[lexitem])

		# TODO(astory): make dynamic?
		for i in range(BOOTSTRAP_REPS):
			classified = classify(train,test)
			train = bootstrap(train, test, classified)

		senses.extend(classify(train,test))
	return senses

if __name__ == '__main__':
	# command line options
	parser = OptionParser()
	parser.add_option("-i", "--fin", dest="fin",
					  help="Name of file containing test data")
	parser.add_option("-d", "--dir", dest="dir", default="nltk_data",
					  help="Directory to look for nltk data")
	parser.add_option("-n", "--naive", action="store_const",
					  const=nltk.NaiveBayesClassifier, dest="classifier",
					  help="Use the naive Bayes classifier")
	parser.add_option("-t", "--tree", action="store_const",
					  const=nltk.DecisionTreeClassifier, dest="classifier",
					  help="Use the decision tree classifier, implies no\
					  probability measurements")
#	parser.add_option("-m", "--maxentropy", action="store_const",
#					  const=nltk.MaxentClassifier, dest="classifier", help="Use\
#					  the maximum entropy classifier")
	parser.add_option("-p", "--use_probs", dest="use_probs", default=False,
					  action="store_true", help="Enable probability based\
					  confidence measurements")
	parser.add_option("-c", "--cutoff_prob", dest="cutoff_prob", default=.5,
					  action="store", help="Unknown probability cutoff")
	parser.add_option("-b", "--bootstrap", dest="bootstrap", default=0,
					  type="int", action="store",
					  help="Number of bootstrapping iterations, defaults to 0,\
					  a value > 0 implies -p, and precludes the use of -t")
	parser.add_option("-o", "--bootstrap_cutoff", dest="bootstrap_cutoff",
					  default=.8, action="store", help="Bootstrapping\
					  probability cutoff")

	# feature extractor options
	parser.add_option("-l", "--colocation", dest="colocation",default=False,
					  action="store_true", help="Enable colocation feature\
					  extractor")
	parser.add_option("-r", "--cooccurrence", dest="cooccurrence", default=False,
					  action="store_true",
					  help="Enable cooccurrence feature extractor")
	parser.add_option("-e", "--base", dest="base_word", default=False,
					  action="store_true",
					  help="Enable base word feature extractor")
	parser.add_option("-s", "--sentence_len", dest="sentence_len", default=False,
					  action="store_true",
					  help="Enable sentence length feature extractor")

	(options, args) = parser.parse_args()

	nltk.data.path[0]=os.path.relpath(options.dir)

	USE_PROBS = options.use_probs
	USE_COLOCATION = options.colocation
	USE_COOCCURRENCE = options.cooccurrence
	USE_BASE_WORD = options.base_word

	CLASSIFIER=nltk.NaiveBayesClassifier
	CLASSIFIER=options.classifier
	CUTOFF_PROB=options.cutoff_prob
	BOOTSTRAP_CUTOFF_PROB=options.bootstrap_cutoff
	BOOTSTRAP_REPS=options.bootstrap
	if BOOTSTRAP_REPS > 0:
		USE_PROBS = True
	if CLASSIFIER == nltk.DecisionTreeClassifier and USE_PROBS:
		raise Exception("Decision tree classifier does not support probability\
		measures")

	items = senseval.fileids()
	tests = pairing.parse_file("EnglishLS.test/EnglishLS.test")
	senses = batch_classify(items, tests)

	f = open('answers.txt')
	l = []
	for line in f:
	  l.append(line)
	for x in range(len(senses)):
	  print(l[x].rstrip().rstrip('\n') + " " +\
		(senses[x]['sense'] if senses[x]['prob'] > CUTOFF_PROB else 'U'))
	f.close()
