a = ['httpd', 'mysql', 'varnish', 'php-fpm']
b = ['httpd', 'php-fpm', 'php-fpm', 'httpd', 'httpd', 'varnish', 'mysql', 'varnish', 'php-fpm']

def filter_(x, y):
	count_test = []
	count_test = dict((i, b.count(i)) for i in b)
	print b

print filter_(a, b)
