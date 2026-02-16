/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 * 
 * PATTERN: Get By Field With Join Query Function
 *
 * Retrieves records by a field value with related data via JOINs
 */

const db = require('../../connection');

/**
 * Get orders by customer ID with details
 */
export async function getOrdersByCustomerIdWithDetails(customerId) {
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
    WHERE orders.customer_id = $1
  `;
  const { rows } = await db.query(SQL, [customerId]);
  return rows;
}