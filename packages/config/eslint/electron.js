/** @type {import('eslint').Linter.Config} */
module.exports = {
  extends: ['./base.js'],
  env: {
    node: true,
    browser: false,
  },
  rules: {
    'no-console': 'off',
  },
};
