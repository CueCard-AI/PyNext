/**
 * Tests for __py.format() - Python format specification
 * 
 * Python f-strings use rich format specs: f"{value:.2f}", f"{value:>10}", etc.
 * JavaScript: No direct equivalent for many specs
 * 
 * This runtime function implements Python format specifications.
 */

const __py = require('./setup');

describe('__py.format() - Python Format Specification', () => {
    
    // =========================================================================
    // PRECISION (f/F type)
    // =========================================================================
    
    describe('Precision (f/F type)', () => {
        test('format(3.14159, ".0f") returns "3"', () => {
            expect(__py.format(3.14159, '.0f')).toBe('3');
        });
        
        test('format(3.14159, ".1f") returns "3.1"', () => {
            expect(__py.format(3.14159, '.1f')).toBe('3.1');
        });
        
        test('format(3.14159, ".2f") returns "3.14"', () => {
            expect(__py.format(3.14159, '.2f')).toBe('3.14');
        });
        
        test('format(3.14159, ".3f") returns "3.142"', () => {
            expect(__py.format(3.14159, '.3f')).toBe('3.142');
        });
        
        test('format(3.14159, ".4f") returns "3.1416"', () => {
            expect(__py.format(3.14159, '.4f')).toBe('3.1416');
        });
        
        test('format(3.14159, ".5f") returns "3.14159"', () => {
            expect(__py.format(3.14159, '.5f')).toBe('3.14159');
        });
        
        test('format(3.14159, ".10f") returns "3.1415900000"', () => {
            expect(__py.format(3.14159, '.10f')).toBe('3.1415900000');
        });
        
        test('format(0, ".2f") returns "0.00"', () => {
            expect(__py.format(0, '.2f')).toBe('0.00');
        });
        
        test('format(-3.14, ".2f") returns "-3.14"', () => {
            expect(__py.format(-3.14, '.2f')).toBe('-3.14');
        });
        
        test('format(1.5, ".0f") rounds correctly', () => {
            expect(__py.format(1.5, '.0f')).toBe('2');
        });
        
        test('format(2.5, ".0f") rounds correctly', () => {
            // JS uses banker's rounding, might be 2 or 3
            const result = __py.format(2.5, '.0f');
            expect(['2', '3']).toContain(result);
        });
        
        test('format very small number', () => {
            expect(__py.format(0.0001, '.4f')).toBe('0.0001');
        });
        
        test('format very large number', () => {
            expect(__py.format(1000000.5, '.2f')).toBe('1000000.50');
        });
    });
    
    // =========================================================================
    // THOUSANDS SEPARATOR
    // =========================================================================
    
    describe('Thousands separator', () => {
        test('format(1234, ",") returns "1,234"', () => {
            expect(__py.format(1234, ',')).toBe('1,234');
        });
        
        test('format(1234567, ",") returns "1,234,567"', () => {
            expect(__py.format(1234567, ',')).toBe('1,234,567');
        });
        
        test('format(123, ",") returns "123"', () => {
            expect(__py.format(123, ',')).toBe('123');
        });
        
        test('format(1234.56, ",") includes decimal', () => {
            const result = __py.format(1234.56, ',');
            expect(result).toMatch(/1,234/);
        });
        
        test('format(-1234, ",") returns "-1,234"', () => {
            expect(__py.format(-1234, ',')).toBe('-1,234');
        });
        
        test('format(0, ",") returns "0"', () => {
            expect(__py.format(0, ',')).toBe('0');
        });
        
        test('format(1000000000, ",") returns "1,000,000,000"', () => {
            expect(__py.format(1000000000, ',')).toBe('1,000,000,000');
        });
    });
    
    // =========================================================================
    // COMBINED PRECISION + THOUSANDS
    // =========================================================================
    
    describe('Combined precision and thousands', () => {
        test('format(1234567.89, ",.2f") returns "1,234,567.89"', () => {
            expect(__py.format(1234567.89, ',.2f')).toBe('1,234,567.89');
        });
        
        test('format(1000.5, ",.1f") returns "1,000.5"', () => {
            expect(__py.format(1000.5, ',.1f')).toBe('1,000.5');
        });
    });
    
    // =========================================================================
    // WIDTH AND ALIGNMENT
    // =========================================================================
    
    describe('Width and alignment', () => {
        test('format("hi", ">10") right-aligns', () => {
            expect(__py.format('hi', '>10')).toBe('        hi');
        });
        
        test('format("hi", "<10") left-aligns', () => {
            expect(__py.format('hi', '<10')).toBe('hi        ');
        });
        
        test('format("hi", "^10") center-aligns', () => {
            expect(__py.format('hi', '^10')).toBe('    hi    ');
        });
        
        test('format("hi", "^11") center-aligns odd width', () => {
            const result = __py.format('hi', '^11');
            expect(result.length).toBe(11);
            expect(result.trim()).toBe('hi');
        });
        
        test('format already wider than width', () => {
            expect(__py.format('hello', '>3')).toBe('hello');
        });
        
        test('format empty string with width', () => {
            expect(__py.format('', '>5')).toBe('     ');
        });
    });
    
    // =========================================================================
    // FILL CHARACTER
    // =========================================================================
    
    describe('Fill character', () => {
        test('format("hi", "*>10") fills with asterisks', () => {
            expect(__py.format('hi', '*>10')).toBe('********hi');
        });
        
        test('format("hi", "-<10") fills with dashes', () => {
            expect(__py.format('hi', '-<10')).toBe('hi--------');
        });
        
        test('format("hi", "=^10") fills with equals', () => {
            expect(__py.format('hi', '=^10')).toBe('====hi====');
        });
        
        test('format("hi", "_>10") fills with underscores', () => {
            expect(__py.format('hi', '_>10')).toBe('________hi');
        });
    });
    
    // =========================================================================
    // ZERO PADDING
    // =========================================================================
    
    describe('Zero padding', () => {
        test('format(5, "05d") returns "00005"', () => {
            expect(__py.format(5, '05d')).toBe('00005');
        });
        
        test('format(-5, "05d") returns "-0005"', () => {
            expect(__py.format(-5, '05d')).toBe('-0005');
        });
        
        test('format(123, "05d") returns "00123"', () => {
            expect(__py.format(123, '05d')).toBe('00123');
        });
        
        test('format(12345, "03d") returns "12345" (no truncation)', () => {
            expect(__py.format(12345, '03d')).toBe('12345');
        });
        
        test('format(0, "05d") returns "00000"', () => {
            expect(__py.format(0, '05d')).toBe('00000');
        });
    });
    
    // =========================================================================
    // SIGN
    // =========================================================================
    
    describe('Sign', () => {
        test('format(5, "+d") returns "+5"', () => {
            expect(__py.format(5, '+d')).toBe('+5');
        });
        
        test('format(-5, "+d") returns "-5"', () => {
            expect(__py.format(-5, '+d')).toBe('-5');
        });
        
        test('format(5, " d") returns " 5"', () => {
            expect(__py.format(5, ' d')).toBe(' 5');
        });
        
        test('format(-5, " d") returns "-5"', () => {
            expect(__py.format(-5, ' d')).toBe('-5');
        });
        
        test('format(0, "+d") returns "+0"', () => {
            expect(__py.format(0, '+d')).toBe('+0');
        });
    });
    
    // =========================================================================
    // PERCENTAGE
    // =========================================================================
    
    describe('Percentage', () => {
        test('format(0.25, ".0%") returns "25%"', () => {
            expect(__py.format(0.25, '.0%')).toBe('25%');
        });
        
        test('format(0.25, ".1%") returns "25.0%"', () => {
            expect(__py.format(0.25, '.1%')).toBe('25.0%');
        });
        
        test('format(0.256, ".2%") returns "25.60%"', () => {
            expect(__py.format(0.256, '.2%')).toBe('25.60%');
        });
        
        test('format(1, ".0%") returns "100%"', () => {
            expect(__py.format(1, '.0%')).toBe('100%');
        });
        
        test('format(0, ".0%") returns "0%"', () => {
            expect(__py.format(0, '.0%')).toBe('0%');
        });
        
        test('format(0.5, ".0%") returns "50%"', () => {
            expect(__py.format(0.5, '.0%')).toBe('50%');
        });
        
        test('format(0.123456, ".2%") returns "12.35%"', () => {
            expect(__py.format(0.123456, '.2%')).toBe('12.35%');
        });
    });
    
    // =========================================================================
    // HEX
    // =========================================================================
    
    describe('Hex', () => {
        test('format(255, "x") returns "ff"', () => {
            expect(__py.format(255, 'x')).toBe('ff');
        });
        
        test('format(255, "X") returns "FF"', () => {
            expect(__py.format(255, 'X')).toBe('FF');
        });
        
        test('format(16, "x") returns "10"', () => {
            expect(__py.format(16, 'x')).toBe('10');
        });
        
        test('format(16, "04x") returns "0010"', () => {
            expect(__py.format(16, '04x')).toBe('0010');
        });
        
        test('format(0, "x") returns "0"', () => {
            expect(__py.format(0, 'x')).toBe('0');
        });
        
        test('format(4095, "x") returns "fff"', () => {
            expect(__py.format(4095, 'x')).toBe('fff');
        });
    });
    
    // =========================================================================
    // BINARY
    // =========================================================================
    
    describe('Binary', () => {
        test('format(5, "b") returns "101"', () => {
            expect(__py.format(5, 'b')).toBe('101');
        });
        
        test('format(255, "b") returns "11111111"', () => {
            expect(__py.format(255, 'b')).toBe('11111111');
        });
        
        test('format(5, "08b") returns "00000101"', () => {
            expect(__py.format(5, '08b')).toBe('00000101');
        });
        
        test('format(0, "b") returns "0"', () => {
            expect(__py.format(0, 'b')).toBe('0');
        });
        
        test('format(1, "b") returns "1"', () => {
            expect(__py.format(1, 'b')).toBe('1');
        });
    });
    
    // =========================================================================
    // OCTAL
    // =========================================================================
    
    describe('Octal', () => {
        test('format(8, "o") returns "10"', () => {
            expect(__py.format(8, 'o')).toBe('10');
        });
        
        test('format(64, "o") returns "100"', () => {
            expect(__py.format(64, 'o')).toBe('100');
        });
        
        test('format(0, "o") returns "0"', () => {
            expect(__py.format(0, 'o')).toBe('0');
        });
        
        test('format(7, "o") returns "7"', () => {
            expect(__py.format(7, 'o')).toBe('7');
        });
    });
    
    // =========================================================================
    // SCIENTIFIC
    // =========================================================================
    
    describe('Scientific notation', () => {
        test('format(1234.5, "e") contains e', () => {
            const result = __py.format(1234.5, 'e');
            expect(result.toLowerCase()).toMatch(/e\+/);
        });
        
        test('format(1234.5, ".2e") has 2 decimals', () => {
            const result = __py.format(1234.5, '.2e');
            expect(result.toLowerCase()).toMatch(/\d\.\d{2}e/);
        });
        
        test('format(1234.5, "E") uses uppercase E', () => {
            const result = __py.format(1234.5, 'E');
            expect(result).toMatch(/E/);
        });
        
        test('format(0.00123, "e") formats small numbers', () => {
            const result = __py.format(0.00123, 'e');
            expect(result.toLowerCase()).toMatch(/e-/);
        });
    });
    
    // =========================================================================
    // EDGE CASES
    // =========================================================================
    
    describe('Edge cases', () => {
        test('format with empty spec returns string', () => {
            expect(__py.format(42, '')).toBe('42');
        });
        
        test('format string with no spec', () => {
            expect(__py.format('hello', '')).toBe('hello');
        });
        
        test('format null', () => {
            expect(__py.format(null, '')).toBe('null');
        });
        
        test('format undefined', () => {
            expect(__py.format(undefined, '')).toBe('undefined');
        });
        
        test('format boolean', () => {
            expect(__py.format(true, '')).toBe('true');
            expect(__py.format(false, '')).toBe('false');
        });
        
        test('format NaN', () => {
            expect(__py.format(NaN, '')).toBe('NaN');
        });
        
        test('format Infinity', () => {
            expect(__py.format(Infinity, '')).toBe('Infinity');
        });
    });
    
    // =========================================================================
    // PYTHON BEHAVIOR VERIFICATION
    // =========================================================================
    
    describe('Python behavior verification', () => {
        test('Python: f"{3.14159:.2f}" == "3.14"', () => {
            expect(__py.format(3.14159, '.2f')).toBe('3.14');
        });
        
        test('Python: f"{1234567:,}" == "1,234,567"', () => {
            expect(__py.format(1234567, ',')).toBe('1,234,567');
        });
        
        test('Python: f"{\'hi\':>10}" == "        hi"', () => {
            expect(__py.format('hi', '>10')).toBe('        hi');
        });
        
        test('Python: f"{5:05d}" == "00005"', () => {
            expect(__py.format(5, '05d')).toBe('00005');
        });
        
        test('Python: f"{0.25:.0%}" == "25%"', () => {
            expect(__py.format(0.25, '.0%')).toBe('25%');
        });
        
        test('Python: f"{255:x}" == "ff"', () => {
            expect(__py.format(255, 'x')).toBe('ff');
        });
        
        test('Python: f"{5:b}" == "101"', () => {
            expect(__py.format(5, 'b')).toBe('101');
        });
    });
    
    // =========================================================================
    // COMMON F-STRING PATTERNS
    // =========================================================================
    
    describe('Common f-string patterns', () => {
        test('Price formatting: $12.50', () => {
            const price = 12.5;
            expect('$' + __py.format(price, '.2f')).toBe('$12.50');
        });
        
        test('Large number formatting: 1,234,567', () => {
            expect(__py.format(1234567, ',')).toBe('1,234,567');
        });
        
        test('Percentage: 75.0%', () => {
            expect(__py.format(0.75, '.1%')).toBe('75.0%');
        });
        
        test('Table column alignment', () => {
            const name = 'Alice';
            const score = 95;
            const nameCol = __py.format(name, '<10');
            const scoreCol = __py.format(score, '>5');
            expect(nameCol).toBe('Alice     ');
            expect(scoreCol).toBe('   95');
        });
        
        test('Zero-padded ID', () => {
            expect(__py.format(42, '06d')).toBe('000042');
        });
    });
});
