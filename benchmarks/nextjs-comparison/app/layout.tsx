export const metadata = {
  title: 'Linear Clone - Next.js Benchmark',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              window.__BENCH__ = {
                pageStart: performance.now(),
                hydrationStart: null,
                hydrationEnd: null,
              };
            `,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
