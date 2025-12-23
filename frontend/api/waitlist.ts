import { neon } from "@neondatabase/serverless";

// Artificial base count to show social proof
const BASE_COUNT = 37;

export default async function handler(
  req: { method?: string; body?: { name?: string; email?: string } },
  res: { status: (code: number) => { json: (data: unknown) => void } }
) {
  const sql = neon(process.env.DATABASE_URL!);

  // GET - Return waitlist count
  if (req.method === "GET") {
    try {
      const result = await sql`SELECT COUNT(*) as count FROM waitlist`;
      const dbCount = parseInt(result[0].count as string, 10) || 0;
      return res.status(200).json({ count: BASE_COUNT + dbCount });
    } catch (error) {
      console.error("Waitlist count error:", error);
      return res.status(200).json({ count: BASE_COUNT });
    }
  }

  // POST - Add to waitlist
  if (req.method === "POST") {
    try {
      const { name, email } = req.body || {};

      // Validate input
      if (!name || typeof name !== "string" || name.trim().length === 0) {
        return res.status(400).json({ error: "Name is required" });
      }

      if (!email || typeof email !== "string" || !email.includes("@")) {
        return res.status(400).json({ error: "Valid email is required" });
      }

      // Insert into waitlist (ignore if email already exists)
      await sql`
        INSERT INTO waitlist (name, email, created_at)
        VALUES (${name.trim()}, ${email.trim().toLowerCase()}, NOW())
        ON CONFLICT (email) DO NOTHING
      `;

      // Return updated count
      const result = await sql`SELECT COUNT(*) as count FROM waitlist`;
      const dbCount = parseInt(result[0].count as string, 10) || 0;

      return res.status(200).json({ success: true, count: BASE_COUNT + dbCount });
    } catch (error) {
      console.error("Waitlist error:", error);
      return res.status(500).json({ error: "Failed to join waitlist" });
    }
  }

  return res.status(405).json({ error: "Method not allowed" });
}
