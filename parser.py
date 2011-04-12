#!/usr/bin/env python
import os
os.environ['MALTPARSERHOME']='MaltParser/malt-1.2'
import nltk
import nltk.parse.malt as malt

m = malt.MaltParser()
m.train_from_file('MaltParser/engmalt.linear.mco')

STR2 = "Do you know what it is ,  and where I can get one ?  We suspect you had seen the Terrex Autospade ,  which is made by Wolf Tools .  It is quite a hefty spade , with bicycle - type handlebars and a sprung lever at the rear , which you step on to activate it . Used correctly ,  you should n't have to bend your back during general digging ,  although it wo n't lift out the soil and put in a barrow if you need to move it !  If gardening tends to give you backache ,  remember to take plenty of rest periods during the day ,  and never try to lift more than you can easily cope with ."
def parse(pos, context, d):
	tree = m.parse(" ".join(context))
	l = tree.nodelist
	deps = l[pos+1]['deps']
	if len(deps) > 0:
		dep = l[deps[0]]['word']
	else:
		dep = ""
	d['dependency'] = dep
