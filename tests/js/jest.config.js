/**
 * Jest Configuration for PyNext JavaScript Tests
 */

module.exports = {
    testEnvironment: 'jsdom',
    testMatch: ['**/*.test.js'],
    setupFilesAfterEnv: ['./setup.js'],
    verbose: true,
    collectCoverageFrom: [
        '../../pynext/runtime/**/*.js',
        '!../../pynext/runtime/min/**',
    ],
    coverageDirectory: './coverage',
    coverageReporters: ['text', 'lcov'],
    moduleFileExtensions: ['js'],
};

