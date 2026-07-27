'use strict';

/**
 * Validação de contrato dos endpoints.
 *
 * Sobe a aplicação refatorada em uma porta efêmera com banco em memória e
 * exercita os 3 endpoints, conferindo status code, Content-Type, corpo e — nos
 * casos de erro — as mensagens herdadas do código original, que a refatoração
 * preserva.
 *
 * Uso: npm run validate
 */

process.env.NODE_ENV = 'test';
process.env.DATABASE_PATH = ':memory:';
process.env.SEED_DATABASE = 'true';
process.env.PAYMENT_GATEWAY_KEY = 'pk_test_validacao';

const { bootstrap } = require('../src/app');

const silentLogger = { log() {}, warn() {}, error() {} };

let total = 0;
const failures = [];

function check(name, problems) {
    total += 1;
    const errors = problems.filter(Boolean);
    const mark = errors.length === 0 ? 'ok   ' : 'FALHA';
    console.log(`  [${mark}] ${name}${errors.length ? `  -> ${errors.join('; ')}` : ''}`);
    if (errors.length) failures.push(name);
}

const expectStatus = (res, expected) =>
    res.status !== expected ? `status ${res.status} != ${expected}` : null;

const expectText = (body, expected) =>
    body !== expected ? `corpo ${JSON.stringify(body)} != ${JSON.stringify(expected)}` : null;

const expectJson = (body, expected) => {
    const actual = JSON.stringify(body);
    const wanted = JSON.stringify(expected);
    return actual !== wanted ? `json ${actual} != ${wanted}` : null;
};

const expectKeys = (body, keys) => {
    const actual = Object.keys(body ?? {}).sort();
    const wanted = [...keys].sort();
    return String(actual) !== String(wanted) ? `chaves ${actual} != ${wanted}` : null;
};

const expectContentType = (res, fragment) =>
    !(res.headers.get('content-type') ?? '').includes(fragment)
        ? `content-type "${res.headers.get('content-type')}" sem "${fragment}"`
        : null;

async function main() {
    const { app, db } = await bootstrap({ logger: silentLogger });
    const server = await new Promise((resolve) => {
        const s = app.listen(0, () => resolve(s));
    });
    const baseUrl = `http://127.0.0.1:${server.address().port}`;

    const post = async (path, body) => {
        const res = await fetch(`${baseUrl}${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: typeof body === 'string' ? body : JSON.stringify(body)
        });
        return res;
    };
    const get = (path) => fetch(`${baseUrl}${path}`);
    const del = (path) => fetch(`${baseUrl}${path}`, { method: 'DELETE' });

    const CHECKOUT_OK = {
        usr: 'Guilherme',
        eml: 'gui@fullcycle.com.br',
        pwd: 'senhaforte',
        c_id: 2,
        card: '4111222233334444'
    };
    const CHECKOUT_DENIED = {
        usr: 'João',
        eml: 'joao@teste.com',
        pwd: '123',
        c_id: 1,
        card: '5111222233334444'
    };

    console.log('\n== POST /api/checkout (caminho feliz) ==');
    let res = await post('/api/checkout', CHECKOUT_OK);
    let body = await res.json();
    check('200 + { msg, enrollment_id }', [
        expectStatus(res, 200),
        expectContentType(res, 'application/json'),
        expectKeys(body, ['msg', 'enrollment_id']),
        expectJson(body, { msg: 'Sucesso', enrollment_id: 2 })
    ]);

    res = await post('/api/checkout', { ...CHECKOUT_OK, c_id: 1 });
    body = await res.json();
    check('usuário existente reaproveitado (enrollment_id 3)', [
        expectStatus(res, 200),
        expectJson(body, { msg: 'Sucesso', enrollment_id: 3 })
    ]);

    res = await post('/api/checkout', { usr: 'Sem Senha', eml: 'sem.senha@teste.com', c_id: 2, card: '4111222233334444' });
    check('pwd é opcional, como no legado (200)', [expectStatus(res, 200)]);

    console.log('\n== POST /api/checkout (erros) ==');
    res = await post('/api/checkout', CHECKOUT_DENIED);
    check('cartão não iniciado com 4 -> 400 "Pagamento recusado"', [
        expectStatus(res, 400),
        expectText(await res.text(), 'Pagamento recusado')
    ]);

    res = await post('/api/checkout', { usr: 'x' });
    check('campos obrigatórios ausentes -> 400 "Bad Request"', [
        expectStatus(res, 400),
        expectText(await res.text(), 'Bad Request')
    ]);

    res = await post('/api/checkout', { ...CHECKOUT_OK, eml: 'nao-e-email' });
    check('e-mail inválido -> 400 "Bad Request"', [
        expectStatus(res, 400),
        expectText(await res.text(), 'Bad Request')
    ]);

    res = await post('/api/checkout', { ...CHECKOUT_OK, c_id: 999 });
    check('curso inexistente -> 404 "Curso não encontrado"', [
        expectStatus(res, 404),
        expectText(await res.text(), 'Curso não encontrado')
    ]);

    res = await post('/api/checkout', { ...CHECKOUT_OK, c_id: 'abc' });
    check('c_id não numérico -> 400 "Bad Request"', [
        expectStatus(res, 400),
        expectText(await res.text(), 'Bad Request')
    ]);

    res = await post('/api/checkout', '{"usr":');
    check('JSON malformado -> 400 "Bad Request"', [
        expectStatus(res, 400),
        expectText(await res.text(), 'Bad Request')
    ]);

    console.log('\n== GET /api/admin/financial-report ==');
    res = await get('/api/admin/financial-report');
    body = await res.json();
    check('200 + array de cursos', [
        expectStatus(res, 200),
        expectContentType(res, 'application/json'),
        Array.isArray(body) ? null : 'corpo não é array',
        body.length === 2 ? null : `esperava 2 cursos, veio ${body.length}`
    ]);
    check('formato { course, revenue, students[{ student, paid }] }', [
        expectKeys(body[0], ['course', 'revenue', 'students']),
        expectKeys(body[0].students[0], ['student', 'paid'])
    ]);
    check('agregação correta após 3 checkouts', [
        expectJson(body, [
            {
                course: 'Clean Architecture',
                revenue: 997 * 2,
                students: [
                    { student: 'Leonan', paid: 997 },
                    { student: 'Guilherme', paid: 997 }
                ]
            },
            {
                course: 'Docker',
                revenue: 497 * 2,
                students: [
                    { student: 'Guilherme', paid: 497 },
                    { student: 'Sem Senha', paid: 497 }
                ]
            }
        ])
    ]);

    const first = await (await get('/api/admin/financial-report')).json();
    const second = await (await get('/api/admin/financial-report')).json();
    check('ordem determinística entre chamadas', [
        JSON.stringify(first) === JSON.stringify(second) ? null : 'duas chamadas retornaram ordens diferentes'
    ]);

    console.log('\n== DELETE /api/users/:id ==');
    res = await del('/api/users/abc');
    check('id não numérico -> 400 "Bad Request"', [
        expectStatus(res, 400),
        expectText(await res.text(), 'Bad Request')
    ]);

    res = await del('/api/users/9999');
    check('usuário inexistente -> 404 "Usuário não encontrado"', [
        expectStatus(res, 404),
        expectText(await res.text(), 'Usuário não encontrado')
    ]);

    res = await del('/api/users/1');
    check('remoção -> 200 + texto', [
        expectStatus(res, 200),
        expectContentType(res, 'text/html'),
        expectText(
            await res.text(),
            'Usuário deletado. Matrículas e pagamentos associados foram removidos na mesma transação.'
        )
    ]);

    const [enrollments, payments] = await Promise.all([
        db.get('SELECT COUNT(*) AS total FROM enrollments WHERE user_id = 1'),
        db.get("SELECT COUNT(*) AS total FROM payments WHERE enrollment_id NOT IN (SELECT id FROM enrollments)")
    ]);
    check('sem registros órfãos após o delete (integridade)', [
        enrollments.total === 0 ? null : `${enrollments.total} matrículas órfãs`,
        payments.total === 0 ? null : `${payments.total} pagamentos órfãos`
    ]);

    const afterDelete = await (await get('/api/admin/financial-report')).json();
    check('relatório não mostra mais aluno "Unknown"', [
        JSON.stringify(afterDelete).includes('Unknown') ? 'ainda há aluno Unknown' : null,
        afterDelete.length === 2 ? null : `esperava 2 cursos, veio ${afterDelete.length}`
    ]);

    console.log('\n== rota inexistente ==');
    res = await get('/api/nao-existe');
    check('404 "Rota não encontrada"', [
        expectStatus(res, 404),
        expectText(await res.text(), 'Rota não encontrada')
    ]);

    console.log('\n== segurança / segredos ==');
    check('nenhum segredo literal em src/', [
        await grepSecrets()
    ]);

    server.close();
    await db.close();

    console.log(`\n${total - failures.length}/${total} checks OK`);
    if (failures.length) {
        console.log(`Falhas: ${failures.join(', ')}`);
        process.exitCode = 1;
    }
}

/** Confere que os literais de segredo do legado não voltaram para o código. */
async function grepSecrets() {
    const fs = require('fs/promises');
    const path = require('path');

    const forbidden = ['senha_super_secreta_prod_123', 'pk_live_', 'admin_master', '123456'];
    const found = [];

    const walk = async (dir) => {
        for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
            const full = path.join(dir, entry.name);
            if (entry.isDirectory()) {
                await walk(full);
                continue;
            }
            if (!entry.name.endsWith('.js')) continue;
            const content = await fs.readFile(full, 'utf8');
            for (const secret of forbidden) {
                if (content.includes(secret)) found.push(`${path.relative(process.cwd(), full)}: ${secret}`);
            }
        }
    };

    await walk(path.resolve(__dirname, '..', 'src'));
    return found.length ? found.join(', ') : null;
}

main().catch((error) => {
    console.error('\nErro fatal na validação:', error);
    process.exit(1);
});
