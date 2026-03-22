#!/usr/bin/env node
// ── Dexpert CLI ────────────────────────────────────────

import { Command } from 'commander';

const program = new Command();

program
  .name('dexpert')
  .description('Dexpert AI Multi-Agent System CLI')
  .version('0.1.0');

program
  .command('run <goal>')
  .description('Execute a single task')
  .option('--agent <agent>', 'Target agent: planner, browser, or os')
  .option('--port <port>', 'Engine port', '48765')
  .action(async (goal: string, options: { agent?: string; port: string }) => {
    console.log(`[Dexpert] Running task: "${goal}"`);
    if (options.agent) {
      console.log(`[Dexpert] Target agent: ${options.agent}`);
    }
    console.log(`[Dexpert] Connecting to engine on port ${options.port}...`);
    // TODO: Connect to engine via WebSocket and execute task
    console.log('[Dexpert] Task execution not yet implemented.');
  });

program
  .command('status')
  .description('Show engine health and agent statuses')
  .option('--port <port>', 'Engine port', '48765')
  .action(async (options: { port: string }) => {
    console.log(`[Dexpert] Checking engine status on port ${options.port}...`);
    // TODO: Check engine health via HTTP
    console.log('[Dexpert] Status check not yet implemented.');
  });

program
  .command('interactive')
  .description('Start an interactive REPL session')
  .option('--port <port>', 'Engine port', '48765')
  .action(async (options: { port: string }) => {
    console.log(`[Dexpert] Starting interactive session on port ${options.port}...`);
    // TODO: Start interactive session
    console.log('[Dexpert] Interactive mode not yet implemented.');
  });

program.parse();
