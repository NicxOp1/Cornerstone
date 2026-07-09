interface AudioPlayerProps {
  recordingBlobUrl: string;
}

export function AudioPlayer({ recordingBlobUrl }: AudioPlayerProps) {
  if (!recordingBlobUrl) {
    return (
      <div className="rounded-xl border border-dashed border-gray-300 p-4 text-center text-sm text-gray-400">
        Grabacion no disponible.
      </div>
    );
  }

  return (
    <audio controls className="w-full" src={recordingBlobUrl}>
      Tu navegador no soporta audio HTML5.
    </audio>
  );
}
