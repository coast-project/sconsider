#include "hello.h"
#include <iostream>
#include <vector>
#include <string>
#include <iterator>
#include <algorithm>

int main(int argc, char *argv[]) {
	if(argc > 1) {
		std::vector<std::string> allArgs(argv, argv + argc);
		if (allArgs[1] == "crash") {
			void *pNotToBeFreed = (void*)&allArgs;
			std::free(pNotToBeFreed);
		}
		typedef std::ostream_iterator<std::string> out;
		std::copy(argv+1, argv+argc, out(std::cout, " "));
	} else {
		std::cout << "Hello from SConsider";
	}
	std::cout << std::endl;
	return 0;
}
