#include <cstdint>
#include <iostream>
#include <vector>
#include <numeric>

typedef struct GF65536_t {
	uint16_t v : 16;

	GF65536_t& operator*=(const GF65536_t& rhs)
	{
		v *= rhs.v;
		return *this;
	}

	GF65536_t& operator+=(const GF65536_t& rhs)
	{
		v += rhs.v;
		return *this;
	}
} GF65536;

GF65536 foo(const GF65536& x)
{
	// calculate x^2
	GF65536 res = x;
	res *= x;
	return res;
}


int main(void)
{
	std::vector<GF65536> items = {
		{ 20123 },
		{ 34563 },
		{ 23489 },
		{ 53480 }
	};

	for (auto const& i : items) {
		auto res = foo(i);
		std::cout << res.v << " ";
	}

	return 0;
}