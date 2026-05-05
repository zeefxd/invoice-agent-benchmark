import { executeAll } from './src/interfaces/cli_runner';

const args = process.argv.slice(2);
const debug = args.includes('--debug');

if (debug) {
    console.log('\x1b[1;36m[TRYB DEBUG AKTYWNY]\x1b[0m');
}

executeAll(debug).catch(console.error);