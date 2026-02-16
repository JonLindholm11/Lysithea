/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 * 
 * PATTERN: Get By ID With Join Query Function
 *
 * Retrieves a single record by ID with related data via JOINs
 */

const db = require('../../connection');

/**
 * Get order by ID with customer details
 */
export async function getOrderByIdWithDetails(id) {
  const SQL = `
    SELECT
      orders.id,
      orders.total_amount,
      orders.order_status,
      orders.created_date,
      customers.id AS customer_id,
      customers.company_name,
      customers.contact_name,
      customers.email AS customer_email
    FROM orders
    LEFT JOIN customers ON orders.customer_id = customers.id
    WHERE orders.id = $1
  `;
  const { rows } = await db.query(SQL, [id]);
  return rows[0];
}