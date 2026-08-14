/**
 * primordial-soup DSH cordis plugin.
 *
 * One job: register the `soup-memory` skill through the runtime skill registry,
 * so installing this npm package makes the mechanism available without any
 * manual SKILL.md placement. The skill body is instructions; actually running
 * the bundled scripts is done by the session's existing pwsh/bash tool, exactly
 * as the skill instructs — this plugin duplicates no tool surface.
 *
 * Consumes the host `skills` registry, publishes nothing: no isolate realm
 * needed, and no other service is injected.
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const HERE = dirname(fileURLToPath(import.meta.url))

const SKILL_NAME = 'soup-memory'
const SKILL_DESCRIPTION =
  '原始汤 (primordial-soup) cross-conversation association mechanism: on an explicit trigger, draw weighted-random amino-acid cards and collide them with the current topic, register every draw in the lightning ledger, and settle cards when a topic closes. User-invocable; effective only inside a soup root (a directory containing `_氨基酸库/INDEX.md`).'

function stripFrontmatter(md) {
  const match = /^---\r?\n[\s\S]*?\r?\n---\r?\n/.exec(md)
  if (match === null) return md
  return md.slice(match[0].length)
}

export const name = 'primordial-soup-dsh'
export const inject = []

export function apply(ctx) {
  const skills = ctx.get('skills')
  if (skills === undefined) return
  skills.register({
    name: SKILL_NAME,
    description: SKILL_DESCRIPTION,
    content: stripFrontmatter(readFileSync(join(HERE, 'skill-body.md'), 'utf8')),
    source: 'bundled',
    invocation: { modelInvocable: false, userInvocable: true },
  })
}
