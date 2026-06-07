'use client';

import React from 'react';
import { Track } from 'livekit-client';
import type { LocalParticipant, RemoteParticipant } from 'livekit-client';
import { motion } from 'motion/react';
import {
  type TrackReference,
  VideoTrack,
  useIsSpeaking,
  useParticipantInfo,
  useParticipantTracks,
  useParticipants,
  useVoiceAssistant,
} from '@livekit/components-react';
import { AgentAudioVisualizerBar } from '@/components/agents-ui/agent-audio-visualizer-bar';
import { cn } from '@/lib/shadcn/utils';

type Participant = RemoteParticipant | LocalParticipant;

const ACCENT = '#2563EB';

/** Audio-visualizer config forwarded to the Nuha tile's bar visualizer. */
export interface AgentVisualizerConfig {
  color?: `#${string}`;
  barCount?: number;
}

/** Two-letter monogram from a participant's display name. */
function monogram(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/** Reflow rules: 1 tile fills, 2 side-by-side, 3+ wrap to 2 columns. */
function gridColumnsClass(count: number): string {
  if (count <= 1) return 'grid-cols-1';
  return 'grid-cols-1 sm:grid-cols-2';
}

interface TileShellProps {
  speaking: boolean;
  /** Distinct accent treatment for the AI clone tile. */
  accent?: boolean;
  className?: string;
  children: React.ReactNode;
}

/** Shared tile frame: rounded card, speaking ring, reduced-motion safe. */
function TileShell({ speaking, accent = false, className, children }: TileShellProps) {
  return (
    <div
      data-speaking={speaking}
      className={cn(
        'group relative flex aspect-video min-h-[160px] items-center justify-center overflow-hidden rounded-xl border',
        'bg-card text-card-foreground',
        accent ? 'border-[#2563EB]/40' : 'border-border',
        // Speaking ring — driven by the live audio track. Animated softly; static under reduced motion.
        'transition-shadow duration-200 motion-reduce:transition-none',
        speaking &&
          (accent
            ? 'border-[#2563EB] shadow-[0_0_0_2px_#2563EB,0_0_28px_-2px_#2563EB] motion-safe:animate-pulse'
            : 'border-foreground/40 shadow-[0_0_0_2px_var(--foreground)]'),
        className
      )}
      style={
        accent && speaking
          ? { boxShadow: `0 0 0 2px ${ACCENT}, 0 0 32px -4px ${ACCENT}` }
          : undefined
      }
    >
      {children}
    </div>
  );
}

/** Small label chip pinned bottom-left of a tile. */
function NameChip({ name, badge }: { name: string; badge?: React.ReactNode }) {
  return (
    <div className="pointer-events-none absolute bottom-2 left-2 z-10 flex items-center gap-1.5">
      <span className="bg-background/80 text-foreground rounded-md px-2 py-0.5 text-xs font-medium backdrop-blur-sm">
        {name}
      </span>
      {badge}
    </div>
  );
}

function MicState({ enabled }: { enabled: boolean }) {
  return (
    <div className="absolute top-2 right-2 z-10">
      <span
        className={cn(
          'flex size-7 items-center justify-center rounded-full text-[11px] font-bold',
          enabled ? 'bg-background/80 text-foreground' : 'bg-destructive/15 text-destructive'
        )}
        title={enabled ? 'Microphone on' : 'Microphone off'}
        aria-label={enabled ? 'Microphone on' : 'Microphone off'}
      >
        {enabled ? (
          <svg
            viewBox="0 0 24 24"
            className="size-4"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden
          >
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" x2="12" y1="19" y2="22" />
          </svg>
        ) : (
          <svg
            viewBox="0 0 24 24"
            className="size-4"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden
          >
            <line x1="2" x2="22" y1="2" y2="22" />
            <path d="M18.89 13.23A7.12 7.12 0 0 0 19 12v-2" />
            <path d="M5 10v2a7 7 0 0 0 12 5" />
            <path d="M15 9.34V5a3 3 0 0 0-5.68-1.33" />
            <path d="M9 9v3a3 3 0 0 0 5.12 2.12" />
            <line x1="12" x2="12" y1="19" y2="22" />
          </svg>
        )}
      </span>
    </div>
  );
}

/**
 * The distinct AI clone tile ("Nuha"): monogram avatar + name + "AI clone" badge,
 * with an audio-reactive glow/bars driven by the agent's live audio track.
 */
function AgentTile({
  name,
  audioTrack,
  state,
  speaking,
  color = ACCENT,
  barCount = 5,
}: {
  name: string;
  audioTrack: TrackReference | undefined;
  state: ReturnType<typeof useVoiceAssistant>['state'];
  speaking: boolean;
  color?: `#${string}`;
  barCount?: number;
}) {
  return (
    <TileShell speaking={speaking} accent>
      {/* Soft accent backdrop */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_40%,rgba(37,99,235,0.18),transparent_70%)]"
      />
      <div className="relative z-[1] flex flex-col items-center gap-4">
        <div className="relative flex items-center justify-center">
          {/* Audio-reactive glow ring behind the avatar */}
          <span
            aria-hidden
            data-speaking={speaking}
            className={cn(
              'absolute inset-0 -m-3 rounded-full bg-[#2563EB]/30 blur-xl transition-opacity duration-300 motion-reduce:transition-none',
              speaking ? 'opacity-100 motion-safe:animate-pulse' : 'opacity-0'
            )}
          />
          <div className="relative flex size-16 items-center justify-center rounded-full bg-[#2563EB] text-lg font-semibold text-white">
            {monogram(name)}
          </div>
        </div>
        {/* Reuse the existing bar visualizer, fed by the agent's audio track */}
        <AgentAudioVisualizerBar
          size="sm"
          state={state}
          audioTrack={audioTrack}
          barCount={barCount}
          color={color}
          className="h-7"
        />
      </div>

      <NameChip
        name={name}
        badge={
          <span className="pointer-events-none rounded-md bg-[#2563EB] px-1.5 py-0.5 font-mono text-[10px] font-bold tracking-wider text-white uppercase">
            AI clone
          </span>
        }
      />
    </TileShell>
  );
}

/** A human participant tile: camera if present, else monogram avatar. */
function HumanTile({ participant }: { participant: Participant }) {
  const speaking = useIsSpeaking(participant);
  const info = useParticipantInfo({ participant });
  const cameraTracks = useParticipantTracks([Track.Source.Camera], participant.identity);
  const cameraTrack = cameraTracks.find((t) => !t.publication?.isMuted);

  const isLocal = participant.isLocal;
  const displayName = isLocal ? 'You' : info.name || participant.identity || 'Guest';
  const micEnabled = participant.isMicrophoneEnabled;

  return (
    <TileShell speaking={speaking}>
      {cameraTrack ? (
        <VideoTrack trackRef={cameraTrack} className="absolute inset-0 size-full object-cover" />
      ) : (
        <div className="bg-muted text-muted-foreground flex size-16 items-center justify-center rounded-full text-lg font-semibold">
          {monogram(displayName)}
        </div>
      )}
      <MicState enabled={micEnabled} />
      <NameChip name={displayName} />
    </TileShell>
  );
}

/**
 * Meet/Zoom-style participant grid. The agent-kind participant renders as the
 * distinct "Nuha" AI tile; humans render as simple tiles. Reflows for 1–3 tiles.
 */
export function ParticipantGrid({
  className,
  agentVisualizer,
}: {
  className?: string;
  agentVisualizer?: AgentVisualizerConfig;
}) {
  const { agent, audioTrack, state } = useVoiceAssistant();
  const agentSpeaking = state === 'speaking';
  const participants = useParticipants();

  // The agent appears in useParticipants(); split it out so humans render as plain tiles.
  const agentIdentity = agent?.identity;
  const humans = participants.filter((p) => p.identity !== agentIdentity);

  // The Nuha AI tile is always shown — it's the room's centerpiece and present even
  // before the agent's audio track arrives (it reacts once the live track connects).
  const agentName = agent?.name || 'Nuha';
  const tileCount = 1 + humans.length;

  return (
    <div className={cn('flex h-full w-full items-center justify-center', className)}>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className={cn(
          'grid w-full max-w-3xl gap-3',
          gridColumnsClass(tileCount),
          'motion-reduce:transform-none'
        )}
      >
        <AgentTile
          key="agent"
          name={agentName}
          audioTrack={audioTrack}
          state={state}
          speaking={agentSpeaking}
          color={agentVisualizer?.color}
          barCount={agentVisualizer?.barCount}
        />
        {humans.map((p) => (
          <HumanTile key={p.identity} participant={p} />
        ))}
      </motion.div>
    </div>
  );
}
