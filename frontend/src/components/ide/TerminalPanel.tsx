"use client";
import { useEffect, useRef } from "react";
// eslint-disable-next-line @typescript-eslint/no-require-imports
if (typeof window !== "undefined") require("@xterm/xterm/css/xterm.css");

interface TerminalPanelProps {
  wsUrl: string;
}

export default function TerminalPanel({ wsUrl }: TerminalPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<any>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    let fitAddon: any;

    const init = async () => {
      const { Terminal } = await import("@xterm/xterm");
      const { FitAddon } = await import("@xterm/addon-fit");

      const term = new Terminal({
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        fontSize: 12,
        lineHeight: 1.6,
        letterSpacing: 0.3,
        cursorBlink: true,
        cursorStyle: "bar",
        theme: {
          background:   "#080706",
          foreground:   "#E8DDD0",
          cursor:       "#C9A96E",
          cursorAccent: "#080706",
          black:        "#1a1816",
          red:          "#A87070",
          green:        "#7AAB8A",
          yellow:       "#C9A96E",
          blue:         "#6B8FAF",
          magenta:      "#9B8AAF",
          cyan:         "#6AABB0",
          white:        "#D4C8BC",
          brightBlack:  "#4a4540",
          brightRed:    "#C08080",
          brightGreen:  "#8ABB9A",
          brightYellow: "#D9B97E",
          brightBlue:   "#7B9FBF",
          brightMagenta:"#AB9ABF",
          brightCyan:   "#7ABBC0",
          brightWhite:  "#F5EFE6",
          selectionBackground: "rgba(201,169,110,0.2)",
        },
        allowTransparency: true,
        scrollback: 5000,
        convertEol: true,
      });

      fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(containerRef.current!);
      fitAddon.fit();
      termRef.current = term;

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          term.write("\r\n  \x1b[33mNimbus IDE\x1b[0m  connected to session\r\n\r\n");
        };

        ws.onmessage = (e) => {
          term.write(e.data);
        };

        ws.onerror = () => {
          term.write("\r\n  \x1b[31m×\x1b[0m  WebSocket error\r\n");
        };

        ws.onclose = () => {
          term.write("\r\n  \x1b[2m  session closed\x1b[0m\r\n");
        };

        term.onData((data: string) => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(data);
          }
        });
      } catch {
        term.write(`\r\n  \x1b[31m×\x1b[0m  Could not connect to session\r\n`);
      }

      const ro = new ResizeObserver(() => fitAddon?.fit());
      if (containerRef.current) ro.observe(containerRef.current);

      return () => ro.disconnect();
    };

    init();

    return () => {
      wsRef.current?.close();
      termRef.current?.dispose();
    };
  }, [wsUrl]);

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: "100%", padding: "8px 12px" }}
    />
  );
}
