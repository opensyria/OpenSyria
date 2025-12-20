CXXFLAGS = -O3 -g0
LDFLAGS = $(CXXFLAGS)

# Fuzz testing flags (use clang for sanitizers)
FUZZ_CXX = clang++
FUZZ_CXXFLAGS = -g -O1 -std=c++17 -fsanitize=fuzzer,address,undefined
FUZZ_LDFLAGS = $(FUZZ_CXXFLAGS)

# Detect macOS and add OpenSSL/Boost paths if needed
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    # macOS with Homebrew
    CXXFLAGS += -I/opt/homebrew/opt/openssl/include -I/usr/local/opt/openssl/include
    CXXFLAGS += -I/opt/homebrew/include -I/usr/local/include
    LDFLAGS += -L/opt/homebrew/opt/openssl/lib -L/usr/local/opt/openssl/lib
    LDFLAGS += -L/opt/homebrew/lib -L/usr/local/lib
endif

dnsseed: dns.o opensy.o netbase.o protocol.o db.o main.o util.o
	g++ -pthread $(LDFLAGS) -o dnsseed dns.o opensy.o netbase.o protocol.o db.o main.o util.o -lcrypto

%.o: %.cpp *.h
	g++ -std=c++11 -pthread $(CXXFLAGS) -Wall -Wno-unused -Wno-sign-compare -Wno-reorder -Wno-comment -c -o $@ $<

# Fuzz testing targets (N-02 Audit Fix)
fuzz_dns: fuzz_dns.cpp
	$(FUZZ_CXX) $(FUZZ_CXXFLAGS) -o fuzz_dns fuzz_dns.cpp

fuzz_dns_standalone: fuzz_dns.cpp
	g++ -std=c++17 -g -O1 -DSTANDALONE_TEST -o fuzz_dns_standalone fuzz_dns.cpp

fuzz: fuzz_dns
	@echo "Running DNS fuzz test (Ctrl+C to stop)..."
	@mkdir -p fuzz_corpus fuzz_findings
	./fuzz_dns -max_len=512 -timeout=5 fuzz_corpus fuzz_findings

fuzz-quick: fuzz_dns
	@echo "Running 60-second DNS fuzz test..."
	@mkdir -p fuzz_corpus fuzz_findings
	./fuzz_dns -max_len=512 -timeout=5 -max_total_time=60 fuzz_corpus fuzz_findings

test: fuzz_dns_standalone
	./fuzz_dns_standalone

clean:
	rm -f dnsseed *.o fuzz_dns fuzz_dns_standalone
	rm -rf fuzz_corpus fuzz_findings

.PHONY: clean fuzz fuzz-quick test
