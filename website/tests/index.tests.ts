import chai, { expect } from 'chai';
import chaiAsPromised from 'chai-as-promised';
import { ImportMock } from 'ts-mock-imports';
import { SinonStub, stub } from 'sinon';
import * as index from '../src/index';
import {
  displayInstances,
  logout,
  onLoad,
  setLoggedInElementsVisibility,
  ApiResponse,
  loadTableData,
  reloadData,
  readCredentials,
} from '../src/index';

const jsdon = require('jsdom');

chai.use(chaiAsPromised);

describe('index tests', () => {
  let dataView: any;
  let loginLink: any;
  let dataTbody: any;
  let apiResponse: ApiResponse;
  let expectedTableBody: string;
  let fetchStub: SinonStub<any>;
  let loadTableDataMock: SinonStub<any>;

  before(() => {
    const { JSDOM } = jsdon;
    global.window = new JSDOM(`<!DOCTYPE html>
      <body>
        <a id="loginLink">Login</a>
        <div id="dataView" hidden>
          <ul class="pagination" id="page-bar" hidden>
            <li class="page-item" id="page-more">More</li>
          </ul>
        </div>
        <table class="table table-striped table-hover">
          <tbody id="dataTbody"></tbody>
        </table>
      </body>`).window;
    global.document = global.window.document;
    fetchStub = stub();
    global.fetch = fetchStub;

    dataView = document.getElementById('dataView');
    loginLink = document.getElementById('loginLink');
    dataTbody = document.getElementById('dataTbody');

    process.env.API_DOMAIN = 'https://api.example.com';
    process.env.LOGIN_URL = 'https://cognito';
  });

  beforeEach(() => {
    apiResponse = {
      Instances: [
        {
          Name: 'Name',
          Id: 'i-1',
          Type: 'small',
          State: 'running',
          AZ: 'us-east-1',
          PublicIps: ['192.168.0.1', '192.168.0.2'],
          PrivateIps: ['8.8.8.8'],
        },
        {
          Name: 'i-2',
          Id: 'i-2',
          Type: 'large',
          State: 'stopped',
          AZ: 'us-east-1',
          PublicIps: [],
          PrivateIps: [],
        },
      ],
    };

    expectedTableBody = `<tr>
    <th scope="row">Name</th>
    <td>i-1</td>
    <td>small</td>
    <td>running</td>
    <td>us-east-1</td>
    <td>192.168.0.1\n192.168.0.2</td>
    <td>8.8.8.8</td>
  </tr><tr>
    <th scope="row">i-2</th>
    <td>i-2</td>
    <td>large</td>
    <td>stopped</td>
    <td>us-east-1</td>
    <td></td>
    <td></td>
  </tr>`;
  });

  after(() => {
    delete process.env.API_DOMAIN;
    delete process.env.LOGIN_URL;
  });

  it('setLoggedInElementsVisibility works as expected', async () => {
    setLoggedInElementsVisibility(true);
    expect(dataView.hidden).eq(false);
    expect(loginLink.hidden).eq(true);
  });

  it('displayInstances works as expected', async () => {
    displayInstances(apiResponse.Instances);

    expect(dataTbody.innerHTML).eql(expectedTableBody);
  });

  it('loadTableData works on success', async () => {
    fetchStub.resolves({
      ok: true,
      json: () => ({ ...apiResponse, NextToken: 'page-2' }),
    });
    await loadTableData();

    expect(dataTbody.innerHTML).eql(expectedTableBody);
  });

  it('loadTableData handles failure', async () => {
    fetchStub.resolves({ ok: false, status: 502 });
    setLoggedInElementsVisibility(true);

    await loadTableData();

    expect(loginLink.hidden).eq(true);
  });

  it('loadTableData handles access denied', async () => {
    fetchStub.resolves({ ok: false, status: 401 });
    setLoggedInElementsVisibility(true);
    localStorage.setItem('Authorization', 'Hunter1');

    await loadTableData();

    expect(localStorage.getItem('Authorization')).eq(null);
  });

  it('onLoad sets login link when no hash', async () => {
    await onLoad();

    expect(loginLink.getAttribute('href')).eq('https://cognito');
  });

  it('onLoad shows data when hash', async () => {
    loadTableDataMock = ImportMock.mockFunction(index, 'loadTableData');
    fetchStub.resolves({ ok: true, json: () => apiResponse });
    window.location.hash = '#id=myId';

    await onLoad();

    expect(window.location.hash).eq('');
    expect(dataView.hidden).eq(false);
    expect(loginLink.hidden).eq(true);
    loadTableDataMock.restore();
  });

  [
    ['#id_token=mytoken', 'mytoken'],
    ['', 'Hunter1'],
  ].forEach(([input, expected]) => {
    it('readCredentials works as expected', async () => {
      localStorage.setItem('Authorization', 'Hunter1');

      readCredentials(input);

      expect(localStorage.getItem('Authorization')).eq(expected);
    });
  });

  it('logout works as expected', async () => {
    localStorage.setItem('Authorization', 'Hunter1');

    logout();

    expect(dataView.hidden).eq(true);
    expect(loginLink.hidden).eq(false);
    expect(localStorage.length).eq(0);
    expect(localStorage.getItem('Authorization')).eq(null);
  });

  it('reloadData works as expected', async () => {
    loadTableDataMock = ImportMock.mockFunction(index, 'loadTableData');
    fetchStub.resolves({ ok: true, json: () => apiResponse });
    dataTbody.innerHTML = '';

    await reloadData();

    expect(dataTbody.innerHTML).eq(expectedTableBody);
    loadTableDataMock.restore();
  });
});
