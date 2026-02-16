/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 * 
 * PATTERN: Get With Join Query Function
 *
 * Retrieves records with related data via LEFT JOIN
 */

const db = require('../../connection');

/**
 * Get orders with customer details
 */
export async function getOrdersWithDetails() {
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
  `;
  const { rows } = await db.query(SQL);
  return rows;
}