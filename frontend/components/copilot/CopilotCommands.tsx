"use client";

import { memo } from "react";

type CopilotCommandsProps = {
  commands: string[];
  onCommand: (command: string) => void;
};

export const CopilotCommands = memo(function CopilotCommands({ commands, onCommand }: CopilotCommandsProps) {
  return (
    <div className="copilot-commands" aria-label="Quick Command">
      {commands.map((command) => (
        <button key={command} data-testid={`copilot-command-${command}`} type="button" onClick={() => onCommand(command)}>
          {command}
        </button>
      ))}
    </div>
  );
});
